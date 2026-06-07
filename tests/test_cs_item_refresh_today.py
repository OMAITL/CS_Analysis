# -*- coding: utf-8 -*-
"""CS item analysis: refresh_today vs refresh_crawl behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from market_provider.csqaq.item_analysis import TODAY_KLINE_PAGES, run_cs_item_analysis
from market_provider.csqaq.schemas import CSQAQPlatform, MergedItemOhlcvMeta
from src.stock_analyzer import TrendAnalysisResult


def _empty_meta() -> MergedItemOhlcvMeta:
    return MergedItemOhlcvMeta(
        good_id=769,
        item_name="test",
        market_hash_name="test",
        platform=CSQAQPlatform.YYYP,
        ohlc_source="kline_chart_all",
        volume_source="kline_chart_all_v",
        data_quality="full",
    )


def _fake_trend() -> TrendAnalysisResult:
    return TrendAnalysisResult(code="test")


@pytest.mark.parametrize(
    "refresh_crawl,refresh_today,expected_pages,expected_fail_soft",
    [
        (False, True, TODAY_KLINE_PAGES, True),
        (True, True, 3, False),
        (False, False, None, None),
    ],
)
def test_refresh_kline_calls(refresh_crawl, refresh_today, expected_pages, expected_fail_soft):
    import pandas as pd

    client = MagicMock()
    client.get_item_good.return_value = {
        "goods_info": {"name": "n", "market_hash_name": "m"},
    }
    frame = pd.DataFrame(
        {
            "date": ["2026-06-01"],
            "open": [1.0],
            "high": [1.0],
            "low": [1.0],
            "close": [1.0],
            "volume": [10.0],
            "amount": [10.0],
            "pct_chg": [0.0],
        }
    )

    with patch(
        "market_provider.csqaq.item_analysis.refresh_item_kline_crawl",
        return_value=1,
    ) as refresh_mock, patch(
        "market_provider.csqaq.item_analysis.ItemOhlcvBuilder"
    ) as builder_cls, patch(
        "market_provider.csqaq.item_analysis.StockTrendAnalyzer"
    ) as analyzer_cls, patch(
        "market_provider.csqaq.item_analysis.CSAnalysisStore"
    ):
        builder_cls.return_value.build.return_value = (frame, _empty_meta())
        analyzer_cls.return_value.analyze.return_value = _fake_trend()

        run_cs_item_analysis(
            client=client,
            good_id=769,
            refresh_crawl=refresh_crawl,
            refresh_today=refresh_today,
            kline_pages=3,
            store_result=False,
        )

    if expected_pages is None:
        refresh_mock.assert_not_called()
        return

    refresh_mock.assert_called_once()
    _, kwargs = refresh_mock.call_args
    assert kwargs["kline_pages"] == expected_pages
    if expected_fail_soft is not None:
        assert kwargs.get("fail_soft", False) is expected_fail_soft
