# -*- coding: utf-8 -*-
"""CSQAQ volume crawler – official Open API path."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from market_provider.csqaq.client import CSQAQClient, resolve_price_platform
from market_provider.csqaq.ohlcv_adapter import (
    chart_series_to_daily_ohlcv,
    index_kline_to_ohlcv,
    market_today_iso,
    ms_to_market_date_iso,
)
from market_provider.csqaq.schemas import CSQAQPlatform, GoodIdEntry, IndexKlineBar

logger = logging.getLogger(__name__)


class CSQAQVolumeCrawler:
    """Fetch index / item daily volume rows via CSQAQ Open API."""

    def __init__(self, client: Optional[CSQAQClient] = None) -> None:
        self.client = client or CSQAQClient()

    def crawl_home_index_volumes(
        self,
        *,
        index_ids: Optional[Iterable[str]] = None,
        kline_period: str = "1day",
    ) -> pd.DataFrame:
        """
        Crawl daily volume for sub-indexes shown on https://csqaq.com/home .

        Primary source: ``GET /api/v1/sub/kline`` field ``v``.
        """
        if index_ids is None:
            indexes = self.client.list_sub_indexes()
            index_ids = [str(row["id"]) for row in indexes if row.get("id") is not None]
        name_map = {
            str(row["id"]): str(row.get("name") or row["id"])
            for row in self.client.list_sub_indexes()
        }

        rows: List[Dict[str, Any]] = []
        for index_id in index_ids:
            bars = self.client.get_index_kline(sub_index_id=str(index_id), period=kline_period)  # type: ignore[arg-type]
            frame = index_kline_to_ohlcv(bars)
            if frame.empty:
                logger.warning("index_id=%s returned empty kline", index_id)
                continue
            for _, rec in frame.iterrows():
                rows.append(
                    {
                        "sub_index_id": str(index_id),
                        "sub_index_name": name_map.get(str(index_id), str(index_id)),
                        "date": rec["date"].isoformat() if hasattr(rec["date"], "isoformat") else str(rec["date"]),
                        "volume": float(rec["volume"]),
                        "open": float(rec["open"]),
                        "high": float(rec["high"]),
                        "low": float(rec["low"]),
                        "close": float(rec["close"]),
                        "volume_source": "index_kline_v",
                    }
                )
        return pd.DataFrame(rows)

    def crawl_item_volume(
        self,
        good_id: int,
        *,
        entry: Optional[GoodIdEntry] = None,
        platform: Optional[CSQAQPlatform | str | int] = None,
        period: int = 365,
    ) -> pd.DataFrame:
        """
        Crawl one item's daily volume rows.

        Priority:
        1. ``chartAll`` enterprise K-line ``v`` (if available)
        2. ``/info/chart`` aggregated ``num_data`` (listing proxy, labeled)
        3. ``/info/good`` snapshot ``turnover_number`` (today only)
        """
        resolved_platform = resolve_price_platform(platform)
        platform_name = resolved_platform.name.lower()

        if entry is None:
            detail = self.client.get_item_good(good_id)
            goods = detail.get("goods_info") or {}
            entry = GoodIdEntry(
                id=int(good_id),
                name=str(goods.get("name") or good_id),
                market_hash_name=str(goods.get("market_hash_name") or good_id),
            )

        rows: List[Dict[str, Any]] = []

        kline_bars = self.client.get_item_kline_daily(good_id, platform=resolved_platform)
        if kline_bars:
            rows.extend(
                self._rows_from_kline_bars(
                    kline_bars,
                    good_id=good_id,
                    entry=entry,
                    platform=platform_name,
                    volume_source="item_chart_all_v",
                )
            )

        if not rows:
            chart_rows = self._rows_from_chart_api(
                good_id,
                entry=entry,
                platform=resolved_platform,
                period=period,
            )
            rows.extend(chart_rows)

        snapshot_row = self._snapshot_turnover_row(good_id, entry=entry, platform=platform_name)
        if snapshot_row:
            rows.append(snapshot_row)

        if not rows:
            logger.warning("good_id=%s no volume rows produced", good_id)
        return pd.DataFrame(rows)

    def crawl_items_from_catalog(
        self,
        *,
        page_size: int = 100,
        max_pages: Optional[int] = 3,
        platform: Optional[CSQAQPlatform | str | int] = None,
        period: int = 365,
    ) -> pd.DataFrame:
        """Paginate ``get_page_list`` and crawl each item."""
        frames: List[pd.DataFrame] = []
        for row in self.client.iter_page_list_items(page_size=page_size, max_pages=max_pages):
            good_id = int(row["id"])
            entry = GoodIdEntry(
                id=good_id,
                name=str(row.get("name") or good_id),
                market_hash_name=str(row.get("market_hash_name") or row.get("name") or good_id),
            )
            frame = self.crawl_item_volume(
                good_id,
                entry=entry,
                platform=platform,
                period=period,
            )
            if not frame.empty:
                frames.append(frame)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    @staticmethod
    def _rows_from_kline_bars(
        bars: Iterable[IndexKlineBar],
        *,
        good_id: int,
        entry: GoodIdEntry,
        platform: str,
        volume_source: str,
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for bar in bars:
            rows.append(
                {
                    "good_id": good_id,
                    "item_name": entry.name,
                    "market_hash_name": entry.market_hash_name,
                    "platform": platform,
                    "date": ms_to_market_date_iso(bar.timestamp_ms),
                    "volume": float(bar.volume),
                    "close": float(bar.close),
                    "volume_source": volume_source,
                }
            )
        return rows

    def _rows_from_chart_api(
        self,
        good_id: int,
        *,
        entry: GoodIdEntry,
        platform: CSQAQPlatform,
        period: int,
    ) -> List[Dict[str, Any]]:
        price = self.client.get_item_chart(
            good_id,
            key="sell_price",
            platform=platform,
            period=period,
        )
        frame, meta = chart_series_to_daily_ohlcv(price, volume_source="sell_num")
        if frame.empty:
            return []
        rows: List[Dict[str, Any]] = []
        for _, rec in frame.iterrows():
            rows.append(
                {
                    "good_id": good_id,
                    "item_name": entry.name,
                    "market_hash_name": entry.market_hash_name,
                    "platform": platform.name.lower(),
                    "date": rec["date"].isoformat() if hasattr(rec["date"], "isoformat") else str(rec["date"]),
                    "volume": float(rec["volume"]),
                    "close": float(rec["close"]),
                    "volume_source": meta.volume_source,
                }
            )
        return rows

    def _snapshot_turnover_row(
        self,
        good_id: int,
        *,
        entry: GoodIdEntry,
        platform: str,
    ) -> Optional[Dict[str, Any]]:
        detail = self.client.get_item_good(good_id)
        goods = detail.get("goods_info") or {}
        turnover = goods.get("turnover_number")
        if turnover is None:
            return None
        updated = goods.get("updated_at") or goods.get("period_at")
        if updated:
            date_str = str(updated).split("T", 1)[0]
        else:
            date_str = market_today_iso()
        return {
            "good_id": good_id,
            "item_name": entry.name,
            "market_hash_name": entry.market_hash_name,
            "platform": platform,
            "date": date_str,
            "volume": float(turnover),
            "close": goods.get("buff_sell_price") or goods.get("yyyp_sell_price"),
            "volume_source": "good_turnover_snapshot",
        }
