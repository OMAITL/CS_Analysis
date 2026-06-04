# -*- coding: utf-8 -*-
"""Offline tests for CSQAQ OHLCV adapter."""

from __future__ import annotations

from market_provider.csqaq.ohlcv_adapter import (
    chart_series_to_daily_ohlcv,
    index_kline_to_ohlcv,
    ms_to_market_date,
)
from market_provider.csqaq.schemas import CSQAQChartSeries, CSQAQPlatform, IndexKlineBar


def _ms(day_offset: int) -> int:
    # 2024-01-01 UTC + day_offset days (+ intra-day offsets encoded in caller)
    base = 1_704_067_200_000
    return base + day_offset * 86_400_000


def test_chart_series_to_daily_ohlcv_aggregates_intraday_points():
    price = CSQAQChartSeries(
        good_id=1,
        key="sell_price",
        platform=CSQAQPlatform.BUFF,
        period=30,
        timestamps=[
            _ms(0),
            _ms(0) + 3_600_000,
            _ms(1),
            _ms(1) + 3_600_000,
        ],
        main_data=[100.0, 105.0, 102.0, 98.0],
        num_data=[10, 12, 8, 9],
    )
    volume = CSQAQChartSeries(
        good_id=1,
        key="turnover_number",
        platform=CSQAQPlatform.STEAM,
        period=30,
        timestamps=[_ms(0), _ms(1)],
        main_data=[50.0, 70.0],
    )

    frame, meta = chart_series_to_daily_ohlcv(price, volume_series=volume, volume_source="turnover_number")

    assert len(frame) == 2
    assert meta.volume_source == "turnover_number"
    assert frame.iloc[0]["open"] == 100.0
    assert frame.iloc[0]["high"] == 105.0
    assert frame.iloc[0]["low"] == 100.0
    assert frame.iloc[0]["close"] == 105.0
    assert frame.iloc[0]["volume"] == 50.0
    assert frame.iloc[1]["close"] == 98.0
    assert frame.iloc[1]["volume"] == 70.0


def test_ms_to_market_date_uses_asia_shanghai():
    # CSQAQ K-line bar for 2026-06-03 is stored as 2026-06-02 16:00 UTC.
    assert ms_to_market_date(1_780_416_000_000).isoformat() == "2026-06-03"


def test_index_kline_to_ohlcv_maps_native_bars():
    bars = [
        IndexKlineBar(timestamp_ms=_ms(0), open=10, high=12, low=9, close=11, volume=100),
        IndexKlineBar(timestamp_ms=_ms(1), open=11, high=13, low=10, close=12, volume=200),
    ]
    frame = index_kline_to_ohlcv(bars)
    assert len(frame) == 2
    assert list(frame.columns) == ["date", "open", "high", "low", "close", "volume", "amount", "pct_chg"]
    assert frame.iloc[1]["pct_chg"] > 0
