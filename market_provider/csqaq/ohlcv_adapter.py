# -*- coding: utf-8 -*-
"""Convert CSQAQ chart / index payloads into standard OHLCV DataFrames."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Sequence, Tuple, Union
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from data_provider.base import STANDARD_COLUMNS
from market_provider.csqaq.schemas import (
    CSQAQChartSeries,
    CSQAQPlatform,
    IndexKlineBar,
    ItemOhlcvBuildMeta,
)

VolumeSource = ItemOhlcvBuildMeta.model_fields["volume_source"].annotation
DEFAULT_MARKET_TZ = ZoneInfo("Asia/Shanghai")


def _market_timezone() -> ZoneInfo:
    raw = os.getenv("CSQAQ_MARKET_TIMEZONE", "Asia/Shanghai").strip()
    if not raw:
        return DEFAULT_MARKET_TZ
    try:
        return ZoneInfo(raw)
    except Exception:
        return DEFAULT_MARKET_TZ


def ms_to_market_date(ms: int) -> datetime.date:
    """Calendar date in market local time (default Asia/Shanghai)."""
    return datetime.fromtimestamp(ms / 1000.0, tz=_market_timezone()).date()


def ms_to_market_date_iso(ms: int) -> str:
    return ms_to_market_date(ms).isoformat()


def market_today_iso() -> str:
    return datetime.now(_market_timezone()).date().isoformat()


_ms_to_date = ms_to_market_date


def _normalize_price_points(
    timestamps: Sequence[int],
    prices: Sequence[Optional[float]],
) -> pd.DataFrame:
    rows: List[Tuple[int, datetime.date, float]] = []
    for ts, price in zip(timestamps, prices):
        if price is None:
            continue
        rows.append((int(ts), _ms_to_date(ts), float(price)))
    if not rows:
        return pd.DataFrame(columns=["date", "price"])
    frame = pd.DataFrame(rows, columns=["ts", "date", "price"])
    return frame.sort_values("ts").reset_index(drop=True)[["date", "price"]]


def _normalize_volume_points(
    timestamps: Sequence[int],
    values: Sequence[Optional[Union[int, float]]],
) -> pd.DataFrame:
    """Use end-of-day snapshot for listing counts (num_data), not intraday sum."""
    rows: List[Tuple[int, datetime.date, float]] = []
    for ts, value in zip(timestamps, values):
        if value is None:
            continue
        rows.append((int(ts), _ms_to_date(ts), float(value)))
    if not rows:
        return pd.DataFrame(columns=["date", "volume"])
    frame = pd.DataFrame(rows, columns=["ts", "date", "volume"])
    frame = frame.sort_values("ts")
    grouped = frame.groupby("date", as_index=False)["volume"].last()
    return grouped.sort_values("date").reset_index(drop=True)


def _aggregate_price_to_ohlc(price_frame: pd.DataFrame) -> pd.DataFrame:
    if price_frame.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close"])

    grouped = (
        price_frame.groupby("date")["price"]
        .agg(open="first", high="max", low="min", close="last")
        .reset_index()
    )
    return grouped.sort_values("date").reset_index(drop=True)


def _finalize_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    """Ensure STANDARD_COLUMNS and derived amount / pct_chg."""
    if frame.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    out = frame.copy()
    if "volume" not in out.columns:
        out["volume"] = 0.0
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0.0)
    out["amount"] = out["close"] * out["volume"]
    out["pct_chg"] = out["close"].pct_change().fillna(0.0) * 100.0
    return out[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)


def chart_series_to_daily_ohlcv(
    price_series: CSQAQChartSeries,
    *,
    volume_series: Optional[CSQAQChartSeries] = None,
    volume_source: VolumeSource = "none",
) -> Tuple[pd.DataFrame, ItemOhlcvBuildMeta]:
    """
    Aggregate CSQAQ item chart points into daily OHLCV bars.

    Price OHLC is derived from ``sell_price`` (or other price-like key) samples.
    Volume priority:
    1. ``volume_series`` when provided (typically ``turnover_number`` on primary platform)
    2. ``price_series.num_data`` companion series (sell listing count proxy)
    3. zero volume
    """
    price_points = _normalize_price_points(price_series.timestamps, price_series.main_data)
    ohlc = _aggregate_price_to_ohlc(price_points)

    resolved_volume_source: VolumeSource = "none"
    volume_platform: Optional[CSQAQPlatform] = None
    volume_frame = pd.DataFrame(columns=["date", "volume"])

    if volume_series is not None and volume_series.main_data:
        volume_frame = _normalize_volume_points(
            volume_series.timestamps,
            volume_series.main_data,
        )
        resolved_volume_source = volume_source if volume_source != "none" else "turnover_number"
        volume_platform = volume_series.platform
    elif price_series.num_data:
        volume_frame = _normalize_volume_points(price_series.timestamps, price_series.num_data)
        resolved_volume_source = "sell_num"
        volume_platform = price_series.platform

    if not ohlc.empty and not volume_frame.empty:
        ohlc = ohlc.merge(volume_frame, on="date", how="left")
    elif not ohlc.empty:
        ohlc["volume"] = 0.0

    result = _finalize_ohlcv(ohlc)
    meta = ItemOhlcvBuildMeta(
        good_id=price_series.good_id,
        price_platform=price_series.platform,
        price_key=price_series.key,
        volume_source=resolved_volume_source,
        volume_platform=volume_platform,
        period_days=price_series.period,
        style=price_series.style,
        row_count=len(result),
    )
    return result, meta


def index_kline_to_ohlcv(bars: Iterable[IndexKlineBar]) -> pd.DataFrame:
    """Map native CSQAQ index K-line bars to the shared OHLCV schema."""
    rows = []
    for bar in bars:
        rows.append(
            {
                "date": _ms_to_date(bar.timestamp_ms),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": float(bar.volume),
            }
        )
    if not rows:
        return pd.DataFrame(columns=STANDARD_COLUMNS)
    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return _finalize_ohlcv(frame)


def empty_ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=STANDARD_COLUMNS)
