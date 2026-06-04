# -*- coding: utf-8 -*-
"""Offline tests for CSQAQ daily volume exports."""

from __future__ import annotations

from market_provider.csqaq.schemas import CSQAQChartSeries, CSQAQPlatform, GoodIdEntry, IndexKlineBar
from market_provider.csqaq.volume_export import build_index_daily_volume_frame, build_item_daily_volume_frame


def _ms(day_offset: int) -> int:
    base = 1_704_067_200_000
    return base + day_offset * 86_400_000


def test_build_index_daily_volume_frame_keeps_daily_volume_columns():
    bars = [
        IndexKlineBar(timestamp_ms=_ms(0), open=10, high=12, low=9, close=11, volume=100),
        IndexKlineBar(timestamp_ms=_ms(1), open=11, high=13, low=10, close=12, volume=200),
    ]

    frame = build_index_daily_volume_frame(bars, sub_index_id="1")

    assert list(frame.columns) == ["sub_index_id", "date", "volume", "close", "amount", "pct_chg"]
    assert frame.iloc[0]["sub_index_id"] == "1"
    assert frame.iloc[1]["volume"] == 200


def test_build_item_daily_volume_frame_prefers_turnover_number_series():
    entry = GoodIdEntry(id=135, name="AK-47 | Redline", market_hash_name="AK-47 | Redline (Field-Tested)")
    price = CSQAQChartSeries(
        good_id=135,
        key="sell_price",
        platform=CSQAQPlatform.YYYP,
        period=30,
        timestamps=[_ms(0), _ms(0) + 3_600_000, _ms(1), _ms(1) + 3_600_000],
        main_data=[100.0, 101.0, 102.0, 103.0],
        num_data=[10, 11, 12, 13],
    )
    volume = CSQAQChartSeries(
        good_id=135,
        key="turnover_number",
        platform=CSQAQPlatform.YYYP,
        period=30,
        timestamps=[_ms(0), _ms(1)],
        main_data=[50.0, 70.0],
    )

    frame, meta = build_item_daily_volume_frame(entry, price, volume_series=volume)

    assert frame.iloc[0]["good_id"] == 135
    assert frame.iloc[0]["market_hash_name"] == "AK-47 | Redline (Field-Tested)"
    assert frame.iloc[0]["platform"] == "yyyp"
    assert frame.iloc[1]["volume"] == 70.0
    assert frame.iloc[1]["close"] == 103.0
    assert frame.iloc[1]["volume_source"] == "turnover_number"
    assert meta.volume_source == "turnover_number"


def test_build_item_daily_volume_frame_falls_back_to_sell_num():
    entry = GoodIdEntry(id=246, name="AWP | Asiimov", market_hash_name="AWP | Asiimov (Field-Tested)")
    price = CSQAQChartSeries(
        good_id=246,
        key="sell_price",
        platform=CSQAQPlatform.BUFF,
        period=30,
        timestamps=[_ms(0), _ms(0) + 3_600_000, _ms(1)],
        main_data=[200.0, 202.0, 198.0],
        num_data=[20, 22, 18],
    )

    frame, meta = build_item_daily_volume_frame(entry, price)

    assert frame.iloc[0]["volume"] == 22.0
    assert frame.iloc[1]["volume"] == 18.0
    assert frame.iloc[0]["volume_source"] == "sell_num"
    assert meta.volume_source == "sell_num"
