# -*- coding: utf-8 -*-
"""Helpers for exporting CSQAQ index / item daily volume datasets."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import pandas as pd

from market_provider.csqaq.client import CSQAQClient, resolve_price_platform
from market_provider.csqaq.ohlcv_adapter import chart_series_to_daily_ohlcv, index_kline_to_ohlcv
from market_provider.csqaq.schemas import (
    CSQAQChartSeries,
    CSQAQPlatform,
    GoodIdEntry,
    IndexKlineBar,
    IndexKlinePeriod,
    ItemOhlcvBuildMeta,
)


def build_index_daily_volume_frame(
    bars: Iterable[IndexKlineBar],
    *,
    sub_index_id: str = "1",
) -> pd.DataFrame:
    """Convert native CSQAQ index bars into a daily volume export table."""
    frame = index_kline_to_ohlcv(bars)
    out = frame[["date", "volume", "close", "amount", "pct_chg"]].copy()
    out.insert(0, "sub_index_id", str(sub_index_id))
    return out.reset_index(drop=True)


def build_item_daily_volume_frame(
    entry: GoodIdEntry,
    price_series: CSQAQChartSeries,
    *,
    volume_series: Optional[CSQAQChartSeries] = None,
) -> Tuple[pd.DataFrame, ItemOhlcvBuildMeta]:
    """Convert CSQAQ item chart series into a daily volume export table."""
    frame, meta = chart_series_to_daily_ohlcv(
        price_series,
        volume_series=volume_series,
        volume_source="turnover_number",
    )
    out = frame[["date", "volume", "close", "amount", "pct_chg"]].copy()
    out.insert(0, "platform", price_series.platform.name.lower())
    out.insert(0, "market_hash_name", entry.market_hash_name)
    out.insert(0, "item_name", entry.name)
    out.insert(0, "good_id", int(entry.id))
    out["volume_source"] = meta.volume_source
    return out.reset_index(drop=True), meta


def fetch_index_daily_volume_frame(
    client: CSQAQClient,
    *,
    sub_index_id: str = "1",
    period: IndexKlinePeriod = "1day",
) -> pd.DataFrame:
    """Fetch and normalize index daily volume data."""
    bars = client.get_index_kline(sub_index_id=sub_index_id, period=period)
    return build_index_daily_volume_frame(bars, sub_index_id=sub_index_id)


def fetch_item_daily_volume_frame(
    client: CSQAQClient,
    good_id: int,
    *,
    entry: Optional[GoodIdEntry] = None,
    price_platform: Optional[CSQAQPlatform | str | int] = None,
    period: int = 365,
    style: str = "all_style",
) -> Tuple[pd.DataFrame, ItemOhlcvBuildMeta]:
    """Fetch and normalize one item's daily volume data."""
    resolved_entry = entry or GoodIdEntry(
        id=int(good_id),
        name=str(good_id),
        market_hash_name=str(good_id),
    )
    payload = client.get_item_daily_ohlcv_inputs(
        int(good_id),
        price_platform=resolve_price_platform(price_platform),
        period=period,
        style=style,
        include_turnover_volume=True,
    )
    return build_item_daily_volume_frame(
        resolved_entry,
        payload["price"],
        volume_series=payload.get("volume"),
    )


def fetch_item_daily_volume_by_query(
    client: CSQAQClient,
    query: str,
    *,
    prefer_market_hash_name: Optional[str] = None,
    price_platform: Optional[CSQAQPlatform | str | int] = None,
    period: int = 365,
    style: str = "all_style",
) -> Tuple[GoodIdEntry, pd.DataFrame, ItemOhlcvBuildMeta]:
    """Resolve an item from a human query and fetch its daily volume data."""
    entry = client.resolve_good_id(
        query,
        prefer_market_hash_name=prefer_market_hash_name,
    )
    frame, meta = fetch_item_daily_volume_frame(
        client,
        entry.id,
        entry=entry,
        price_platform=price_platform,
        period=period,
        style=style,
    )
    return entry, frame, meta
