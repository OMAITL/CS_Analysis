# -*- coding: utf-8 -*-
"""Fuse CSQAQ Open API charts with crawler K-line data into analysis-grade OHLCV."""

from __future__ import annotations

import logging
from typing import Optional, Tuple, Union

import pandas as pd

from crawlers.csqaq.store import VolumeCrawlStore
from market_provider.csqaq.client import CSQAQAPIError, CSQAQClient, resolve_price_platform
from market_provider.csqaq.ohlcv_adapter import chart_series_to_daily_ohlcv
from market_provider.csqaq.schemas import (
    CSQAQPlatform,
    DataQuality,
    GoodIdEntry,
    MergedItemOhlcvMeta,
    MergedVolumeSource,
    OhlcSource,
)

logger = logging.getLogger(__name__)

KLINE_VOLUME_SOURCE = "kline_chart_all_v"
STANDARD_COLUMNS = ["date", "open", "high", "low", "close", "volume", "amount", "pct_chg"]


def _normalize_date(value) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _has_kline_ohlc(frame: pd.DataFrame) -> bool:
    needed = ("open", "high", "low", "close")
    if not all(col in frame.columns for col in needed):
        return False
    subset = frame[list(needed)].dropna(how="all")
    return not subset.empty


def _crawl_to_standard(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)
    out = frame.copy()
    out["date"] = out["date"].map(_normalize_date)
    for col in ("open", "high", "low", "close", "volume"):
        if col not in out.columns:
            out[col] = pd.NA
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["amount"] = out["close"] * out["volume"]
    out["pct_chg"] = out["close"].pct_change().fillna(0.0) * 100.0
    return out[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)


def _crawl_row_has_complete_ohlc(crawl_frame: pd.DataFrame, date: str) -> bool:
    if crawl_frame.empty:
        return False
    dates = crawl_frame["date"].map(_normalize_date)
    rows = crawl_frame.loc[dates == date]
    if rows.empty:
        return False
    row = rows.iloc[-1]
    for col in ("open", "high", "low", "close"):
        if col not in row.index or pd.isna(row[col]):
            return False
    return True


def _annotate_rows(
    frame: pd.DataFrame,
    *,
    good_id: int,
    item_name: str,
    market_hash_name: str,
    platform: str,
    ohlc_source: OhlcSource,
    volume_source: MergedVolumeSource,
    data_quality: DataQuality,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    out["good_id"] = int(good_id)
    out["item_name"] = item_name
    out["market_hash_name"] = market_hash_name
    out["platform"] = platform
    out["date"] = out["date"].map(_normalize_date)
    out["ohlc_source"] = ohlc_source
    out["volume_source"] = volume_source
    out["data_quality"] = data_quality
    return out


def _resolve_data_quality(frame: pd.DataFrame, *, has_kline_volume: bool) -> DataQuality:
    if frame.empty:
        return "degraded"
    volume = pd.to_numeric(frame["volume"], errors="coerce").fillna(0.0)
    if has_kline_volume and (volume > 0).any():
        if (volume > 0).all():
            return "full"
        return "degraded"
    if (volume > 0).any():
        return "degraded"
    return "price_only"


def _merge_crawl_and_api(
    crawl_frame: pd.DataFrame,
    api_frame: pd.DataFrame,
    *,
    api_volume_source: MergedVolumeSource,
) -> Tuple[pd.DataFrame, OhlcSource, MergedVolumeSource]:
    crawl_std = _crawl_to_standard(crawl_frame)
    api_std = api_frame.copy()
    if "date" in api_std.columns:
        api_std["date"] = api_std["date"].map(_normalize_date)
    if not crawl_std.empty:
        crawl_std["date"] = crawl_std["date"].map(_normalize_date)

    if crawl_std.empty:
        return api_std, "sell_price_agg", api_volume_source

    if api_std.empty:
        ohlc_source: OhlcSource = "kline_chart_all" if _has_kline_ohlc(crawl_frame) else "sell_price_agg"
        return crawl_std, ohlc_source, KLINE_VOLUME_SOURCE

    crawl_by_date = crawl_std.drop_duplicates("date", keep="last").set_index("date")
    api_by_date = api_std.drop_duplicates("date", keep="last").set_index("date")
    all_dates = sorted(set(crawl_by_date.index) | set(api_by_date.index))

    rows: list[dict] = []
    kline_ohlc_dates = 0
    api_ohlc_dates = 0
    used_kline_volume = False

    for date in all_dates:
        crawl_row = crawl_by_date.loc[date] if date in crawl_by_date.index else None
        api_row = api_by_date.loc[date] if date in api_by_date.index else None

        if _crawl_row_has_complete_ohlc(crawl_frame, date) and crawl_row is not None:
            row = crawl_row.to_dict()
            row["date"] = date
            kline_ohlc_dates += 1
            if float(row.get("volume") or 0) > 0:
                used_kline_volume = True
        elif api_row is not None:
            row = api_row.to_dict()
            row["date"] = date
            api_ohlc_dates += 1
            if crawl_row is not None and not pd.isna(crawl_row.get("volume")):
                row["volume"] = float(crawl_row["volume"])
                if row["volume"] > 0:
                    used_kline_volume = True
        elif crawl_row is not None:
            row = crawl_row.to_dict()
            row["date"] = date
            if not _crawl_row_has_complete_ohlc(crawl_frame, date) and not pd.isna(row.get("close")):
                price = float(row["close"])
                row["open"] = price
                row["high"] = price
                row["low"] = price
                api_ohlc_dates += 1
            if float(row.get("volume") or 0) > 0:
                used_kline_volume = True
        else:
            continue
        rows.append(row)

    merged = _crawl_to_standard(pd.DataFrame(rows))
    if kline_ohlc_dates > 0 and api_ohlc_dates > 0:
        ohlc_source = "mixed"
    elif kline_ohlc_dates > 0:
        ohlc_source = "kline_chart_all"
    else:
        ohlc_source = "sell_price_agg"

    volume_source: MergedVolumeSource = KLINE_VOLUME_SOURCE if used_kline_volume else api_volume_source
    return merged, ohlc_source, volume_source


def build_item_ohlcv_from_api(
    client: CSQAQClient,
    good_id: int,
    *,
    platform: Optional[Union[str, int, CSQAQPlatform]] = None,
    period: int = 365,
) -> Tuple[pd.DataFrame, MergedVolumeSource]:
    resolved = resolve_price_platform(platform)
    try:
        charts = client.get_item_daily_ohlcv_inputs(good_id, price_platform=resolved, period=period)
    except CSQAQAPIError as exc:
        logger.warning("CSQAQ API OHLCV unavailable for good_id=%s (code=%s)", good_id, exc.code)
        return pd.DataFrame(columns=STANDARD_COLUMNS), "none"
    except Exception as exc:
        logger.warning("CSQAQ API OHLCV request failed for good_id=%s: %s", good_id, exc)
        return pd.DataFrame(columns=STANDARD_COLUMNS), "none"
    volume_series = charts.get("volume")
    frame, meta = chart_series_to_daily_ohlcv(
        charts["price"],
        volume_series=volume_series,
        volume_source="turnover_number" if volume_series is not None else "none",
    )
    api_volume_source: MergedVolumeSource
    if meta.volume_source == "turnover_number":
        api_volume_source = "turnover_number"
    elif meta.volume_source == "sell_num":
        api_volume_source = "sell_num"
    else:
        api_volume_source = "none"
    return frame, api_volume_source


class ItemOhlcvBuilder:
    """Merge crawler K-line rows with CSQAQ Open API fallback."""

    def __init__(
        self,
        *,
        client: Optional[CSQAQClient] = None,
        crawl_store: Optional[VolumeCrawlStore] = None,
    ) -> None:
        self.client = client or CSQAQClient()
        self.crawl_store = crawl_store or VolumeCrawlStore()

    def build(
        self,
        good_id: int,
        *,
        entry: Optional[GoodIdEntry] = None,
        platform: Optional[Union[str, int, CSQAQPlatform]] = None,
        period: int = 365,
        prefer_crawl: bool = True,
    ) -> Tuple[pd.DataFrame, MergedItemOhlcvMeta]:
        resolved = resolve_price_platform(platform)
        platform_name = resolved.name.lower()

        if entry is None:
            detail = self.client.get_item_good(good_id)
            goods = detail.get("goods_info") or {}
            entry = GoodIdEntry(
                id=int(good_id),
                name=str(goods.get("name") or good_id),
                market_hash_name=str(goods.get("market_hash_name") or good_id),
            )

        api_frame, api_volume_source = build_item_ohlcv_from_api(
            self.client,
            good_id,
            platform=resolved,
            period=period,
        )
        crawl_frame = pd.DataFrame()
        if prefer_crawl:
            crawl_frame = self.crawl_store.read_item_kline(
                good_id=good_id,
                platform=platform_name,
                volume_source=KLINE_VOLUME_SOURCE,
            )

        crawl_rows = len(crawl_frame)
        api_rows = len(api_frame)

        if prefer_crawl and not crawl_frame.empty:
            merged, ohlc_source, volume_source = _merge_crawl_and_api(
                crawl_frame,
                api_frame,
                api_volume_source=api_volume_source,
            )
        else:
            merged = api_frame.copy()
            ohlc_source = "sell_price_agg"
            volume_source = api_volume_source
            if not crawl_frame.empty:
                logger.info(
                    "good_id=%s crawl rows ignored because prefer_crawl=False",
                    good_id,
                )

        has_kline_volume = (
            prefer_crawl
            and not crawl_frame.empty
            and (pd.to_numeric(crawl_frame.get("volume"), errors="coerce").fillna(0) > 0).any()
        )
        data_quality = _resolve_data_quality(merged, has_kline_volume=has_kline_volume)

        annotated = _annotate_rows(
            merged,
            good_id=good_id,
            item_name=entry.name,
            market_hash_name=entry.market_hash_name,
            platform=platform_name,
            ohlc_source=ohlc_source,
            volume_source=volume_source,
            data_quality=data_quality,
        )

        meta = MergedItemOhlcvMeta(
            good_id=int(good_id),
            item_name=entry.name,
            market_hash_name=entry.market_hash_name,
            platform=resolved,
            ohlc_source=ohlc_source,
            volume_source=volume_source,
            data_quality=data_quality,
            row_count=len(annotated),
            crawl_rows=crawl_rows,
            api_rows=api_rows,
            period_days=period,
        )
        return annotated, meta

    def build_by_query(
        self,
        item_query: str,
        *,
        platform: Optional[Union[str, int, CSQAQPlatform]] = None,
        period: int = 365,
        prefer_crawl: bool = True,
    ) -> Tuple[pd.DataFrame, MergedItemOhlcvMeta]:
        entry = self.client.resolve_good_id(item_query, prefer_market_hash_name=item_query)
        return self.build(
            entry.id,
            entry=entry,
            platform=platform,
            period=period,
            prefer_crawl=prefer_crawl,
        )
