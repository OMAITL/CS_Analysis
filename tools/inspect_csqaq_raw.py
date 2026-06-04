#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect raw CSQAQ chart points vs aggregated OHLCV (debug)."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from market_provider.csqaq import CSQAQClient, chart_series_to_daily_ohlcv  # noqa: E402
from market_provider.csqaq.schemas import CSQAQPlatform  # noqa: E402


def _points_per_day(timestamps):
    from datetime import datetime, timezone

    days = [datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date() for ts in timestamps]
    counts = Counter(days)
    return counts


def main() -> None:
    client = CSQAQClient(enable_cache=True)
    good_id = 135
    for platform in (CSQAQPlatform.YYYP, CSQAQPlatform.BUFF):
        print("=" * 70)
        print(f"platform={platform.name}")
        price = client.get_item_chart(good_id, key="sell_price", platform=platform, period=30)
        print(f"raw points: {len(price.timestamps)}")
        print(f"key={price.key} style={price.style}")
        if price.timestamps:
            print(f"first ts sample: {price.timestamps[:3]}")
            print(f"first prices:    {price.main_data[:3]}")
            if price.num_data:
                print(f"first num_data:  {price.num_data[:3]}")
        counts = _points_per_day(price.timestamps)
        multi = sum(1 for c in counts.values() if c > 1)
        print(f"distinct days: {len(counts)} | days with >1 point: {multi}")
        print("sample days with multiple points:")
        for day, cnt in sorted(counts.items())[-5:]:
            if cnt > 1:
                print(f"  {day}: {cnt} points")

        df, meta = chart_series_to_daily_ohlcv(price)
        print(f"\naggregated OHLCV tail (volume_source={meta.volume_source}):")
        print(df.tail(5).to_string(index=False))
        print()


if __name__ == "__main__":
    main()
