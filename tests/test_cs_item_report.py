# -*- coding: utf-8 -*-
"""Offline tests for CS item report template."""

from __future__ import annotations

from market_provider.csqaq.cs_report import CSItemReportGenerator, _template_report
from market_provider.csqaq.item_analysis import CSItemAnalysisContext
from market_provider.csqaq.schemas import CSQAQPlatform, MergedItemOhlcvMeta
from src.stock_analyzer import TrendAnalysisResult


def _sample_context() -> CSItemAnalysisContext:
    meta = MergedItemOhlcvMeta(
        good_id=769,
        item_name="法玛斯 | 机械工业 (崭新出厂)",
        market_hash_name="FAMAS | Mecha Industries (Factory New)",
        platform=CSQAQPlatform.YYYP,
        ohlc_source="kline_chart_all",
        volume_source="kline_chart_all_v",
        data_quality="full",
        row_count=150,
        crawl_rows=150,
        api_rows=100,
    )
    trend = TrendAnalysisResult(code="FAMAS | Mecha Industries (Factory New)")
    trend.current_price = 934.0
    trend.trend_status = trend.trend_status.__class__("强势多头")
    trend.buy_signal = trend.buy_signal.__class__("持有")
    trend.signal_score = 48
    trend.volume_ratio_5d = 0.52
    trend.ma5 = 861.1
    trend.risk_factors = ["RSI 超买"]
    return CSItemAnalysisContext(
        good_id=769,
        item_name=meta.item_name,
        market_hash_name=meta.market_hash_name,
        platform="yyyp",
        snapshot={"buff_sell_price": 928.0, "yyyp_sell_price": 934.0, "yyyp_sell_num": 563},
        meta=meta,
        trend=trend,
        ohlcv_tail=[{"date": "2026-06-03", "close": 934.0, "volume": 157.0}],
    )


def test_template_report_contains_sections():
    md = _template_report(_sample_context())
    for title in (
        "## 核心结论",
        "## 技术面解读",
        "## 事件与舆论影响",
        "## 风险提示",
        "## 操作建议",
    ):
        assert title in md


def test_generator_falls_back_without_llm(monkeypatch):
    gen = CSItemReportGenerator(analyzer=type("A", (), {"is_available": lambda self: False})())
    md, source = gen.generate(_sample_context())
    assert source == "template"
    assert "769" in md
