# -*- coding: utf-8 -*-
"""CS item analysis: API failure fallback to crawl K-line."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market_provider.csqaq.client import CSQAQAPIError
from market_provider.csqaq.item_analysis import resolve_item_goods_info, run_cs_item_analysis
from market_provider.csqaq.item_ohlcv_builder import build_item_ohlcv_from_api
from market_provider.csqaq.schemas import CSQAQPlatform, MergedItemOhlcvMeta
from src.stock_analyzer import TrendAnalysisResult


def test_resolve_item_goods_info_falls_back_to_catalog():
    client = MagicMock()
    client.get_item_good.side_effect = CSQAQAPIError("unauthorized", code=401)

    catalog_row = MagicMock()
    catalog_row.name = "法玛斯 | 机械工业 (崭新出厂)"
    catalog_row.market_hash_name = "FAMAS | Mecha Industries (Factory New)"

    with patch(
        "src.repositories.cs_item_catalog_repo.CSItemCatalogRepository"
    ) as repo_cls:
        repo_cls.return_value.get_by_good_id.return_value = catalog_row
        goods = resolve_item_goods_info(client, 769)

    assert goods["name"] == "法玛斯 | 机械工业 (崭新出厂)"
    assert "FAMAS" in goods["market_hash_name"]


def test_build_item_ohlcv_from_api_returns_empty_on_401():
    client = MagicMock()
    client.get_item_daily_ohlcv_inputs.side_effect = CSQAQAPIError("unauthorized", code=401)

    frame, volume_source = build_item_ohlcv_from_api(client, 769)

    assert frame.empty
    assert volume_source == "none"


def test_run_cs_item_analysis_uses_crawl_when_api_snapshot_fails():
    client = MagicMock()
    client.get_item_good.side_effect = CSQAQAPIError("unauthorized", code=401)

    frame = pd.DataFrame(
        {
            "date": ["2026-06-01", "2026-06-02"],
            "open": [100.0, 105.0],
            "high": [110.0, 115.0],
            "low": [95.0, 100.0],
            "close": [108.0, 112.0],
            "volume": [50.0, 60.0],
            "amount": [5400.0, 6720.0],
            "pct_chg": [0.0, 3.7],
        }
    )
    meta = MergedItemOhlcvMeta(
        good_id=769,
        item_name="法玛斯 | 机械工业 (崭新出厂)",
        market_hash_name="FAMAS | Mecha Industries (Factory New)",
        platform=CSQAQPlatform.YYYP,
        ohlc_source="kline_chart_all",
        volume_source="kline_chart_all_v",
        data_quality="full",
        crawl_rows=2,
        api_rows=0,
    )
    trend = TrendAnalysisResult(code="FAMAS | Mecha Industries (Factory New)")
    trend.current_price = 112.0
    trend.signal_score = 58
    trend.buy_signal = "偏多观望"

    with patch(
        "market_provider.csqaq.item_analysis.resolve_item_goods_info",
        return_value={"name": "法玛斯 | 机械工业 (崭新出厂)", "market_hash_name": "FAMAS | Mecha Industries (Factory New)"},
    ), patch(
        "market_provider.csqaq.item_analysis.refresh_item_kline_crawl",
        return_value=0,
    ), patch(
        "market_provider.csqaq.item_analysis.ItemOhlcvBuilder"
    ) as builder_cls, patch(
        "market_provider.csqaq.item_analysis.StockTrendAnalyzer"
    ) as analyzer_cls, patch(
        "market_provider.csqaq.item_analysis.CSAnalysisStore"
    ):
        builder_cls.return_value.build.return_value = (frame, meta)
        analyzer_cls.return_value.analyze.return_value = trend

        ctx = run_cs_item_analysis(
            client=client,
            good_id=769,
            refresh_today=False,
            store_result=False,
            fallback_name="法玛斯 | 机械工业 (崭新出厂)",
        )

    assert ctx.good_id == 769
    assert ctx.trend.current_price == 112.0
    assert ctx.snapshot.get("api_snapshot_error")
    assert "crawl_kline" in (ctx.snapshot.get("data_sources") or [])
    assert ctx.snapshot.get("yyyp_sell_price") == 112.0
