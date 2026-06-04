# -*- coding: utf-8 -*-
"""Offline tests for fused CS item OHLCV builder."""

from __future__ import annotations

import pandas as pd

from market_provider.csqaq.item_ohlcv_builder import (
    KLINE_VOLUME_SOURCE,
    _merge_crawl_and_api,
    _resolve_data_quality,
)


def test_merge_prefers_crawl_kline_ohlcv():
    crawl = pd.DataFrame(
        [
            {
                "date": "2026-06-01",
                "open": 800.0,
                "high": 900.0,
                "low": 790.0,
                "close": 880.0,
                "volume": 100.0,
                "volume_source": KLINE_VOLUME_SOURCE,
            },
            {
                "date": "2026-06-02",
                "open": 880.0,
                "high": 920.0,
                "low": 870.0,
                "close": 910.0,
                "volume": 157.0,
                "volume_source": KLINE_VOLUME_SOURCE,
            },
        ]
    )
    api = pd.DataFrame(
        [
            {
                "date": "2026-05-31",
                "open": 700.0,
                "high": 700.0,
                "low": 700.0,
                "close": 700.0,
                "volume": 500.0,
                "amount": 350000.0,
                "pct_chg": 0.0,
            },
            {
                "date": "2026-06-01",
                "open": 750.0,
                "high": 750.0,
                "low": 750.0,
                "close": 750.0,
                "volume": 900.0,
                "amount": 675000.0,
                "pct_chg": 7.14,
            },
        ]
    )

    merged, ohlc_source, volume_source = _merge_crawl_and_api(crawl, api, api_volume_source="sell_num")

    assert ohlc_source == "mixed"
    assert volume_source == KLINE_VOLUME_SOURCE
    assert len(merged) == 3
    june1 = merged[merged["date"] == "2026-06-01"].iloc[0]
    assert june1["close"] == 880.0
    assert june1["volume"] == 100.0
    assert merged.iloc[0]["date"] == "2026-05-31"


def test_merge_overlays_crawl_volume_on_api_when_no_ohlc():
    crawl = pd.DataFrame(
        [
            {"date": "2026-06-02", "close": 910.0, "volume": 157.0, "volume_source": KLINE_VOLUME_SOURCE},
        ]
    )
    api = pd.DataFrame(
        [
            {
                "date": "2026-06-02",
                "open": 910.0,
                "high": 910.0,
                "low": 910.0,
                "close": 910.0,
                "volume": 800.0,
                "amount": 728000.0,
                "pct_chg": 0.0,
            }
        ]
    )

    merged, ohlc_source, volume_source = _merge_crawl_and_api(crawl, api, api_volume_source="sell_num")

    assert ohlc_source == "sell_price_agg"
    assert volume_source == KLINE_VOLUME_SOURCE
    assert merged.iloc[0]["volume"] == 157.0


def test_data_quality_full_with_kline_volume():
    frame = pd.DataFrame({"volume": [10.0, 20.0, 30.0]})
    assert _resolve_data_quality(frame, has_kline_volume=True) == "full"

    partial = pd.DataFrame({"volume": [10.0, 0.0, 30.0]})
    assert _resolve_data_quality(partial, has_kline_volume=True) == "degraded"

    zero = pd.DataFrame({"volume": [0.0, 0.0]})
    assert _resolve_data_quality(zero, has_kline_volume=False) == "price_only"
