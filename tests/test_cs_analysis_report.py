# -*- coding: utf-8 -*-
"""Tests for CS analyzer context and stock-equivalent analyze() path."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from market_provider.csqaq.schemas import CSQAQPlatform, MergedItemOhlcvMeta
from src.analyzer import AnalysisResult
from src.services.cs_analysis_report import (
    analysis_result_to_cs_markdown,
    build_cs_analyzer_context,
    build_cs_gemini_analyzer,
    build_cs_report_payload,
    format_cs_analyzer_user_prompt,
)
from src.stock_analyzer import TrendAnalysisResult, TrendStatus


def _minimal_ctx():
    from market_provider.csqaq.item_analysis import CSItemAnalysisContext

    trend = TrendAnalysisResult(code="cs:1")
    trend.trend_status = TrendStatus.CONSOLIDATION
    meta = MergedItemOhlcvMeta(
        good_id=1,
        item_name="测试刀",
        market_hash_name="Test Knife",
        platform=CSQAQPlatform.YYYP,
        ohlc_source="kline_chart_all",
        volume_source="kline_chart_all_v",
        data_quality="full",
    )
    return CSItemAnalysisContext(
        good_id=1,
        item_name="测试刀",
        market_hash_name="Test Knife",
        platform="yyyp",
        snapshot={"buff_sell_price": 100.0, "yyyp_sell_price": 99.0},
        meta=meta,
        trend=trend,
        ohlcv_tail=[{"date": "2026-01-01", "close": 10.0, "volume": 5}],
        event_intel=[{"title": "Major", "url": "https://example.com"}],
    )


def test_build_cs_analyzer_context_marks_cs_asset():
    ctx = _minimal_ctx()
    payload = build_cs_analyzer_context(ctx)
    assert payload["asset_type"] == "cs_item"
    assert payload["code"] == "cs:1"
    assert "trend_analysis" in payload


def test_format_cs_user_prompt_no_skills_section():
    ctx = _minimal_ctx()
    payload = build_cs_analyzer_context(ctx)
    prompt = format_cs_analyzer_user_prompt(payload, "测试刀", "event text")
    assert "决策仪表盘" in prompt
    assert "event text" in prompt
    assert "激活的交易技能" not in prompt


def test_build_cs_gemini_analyzer_uses_skill_overrides():
    analyzer, state = build_cs_gemini_analyzer(["bull_trend"])
    instructions, policy, legacy = analyzer._get_skill_prompt_sections()
    assert "CS 技能与输入数据映射" in instructions
    assert "CS 饰品交易基线" in policy
    assert legacy is False
    assert state.active_skill_ids == ("bull_trend",)


def test_analysis_result_to_cs_markdown_sections():
    ctx = _minimal_ctx()
    result = AnalysisResult(
        code="cs:1",
        name="测试刀",
        sentiment_score=65,
        trend_prediction="看多",
        operation_advice="持有",
        analysis_summary="观望为主",
        dashboard={
            "core_conclusion": {"one_sentence": "短线观望"},
            "intelligence": {"risk_alerts": ["波动大"]},
        },
    )
    md = analysis_result_to_cs_markdown(result, ctx)
    assert "## 核心结论" in md
    assert "## 操作建议" in md
    assert "短线观望" in md


@patch("src.services.cs_analysis_report.GeminiAnalyzer")
def test_run_cs_item_llm_analysis_calls_analyze(mock_cls):
    from src.services.cs_analysis_report import run_cs_item_llm_analysis

    ctx = _minimal_ctx()
    mock_analyzer = MagicMock()
    mock_analyzer.is_available.return_value = True
    mock_analyzer.analyze.return_value = AnalysisResult(
        code="cs:1",
        name="测试刀",
        sentiment_score=70,
        trend_prediction="看多",
        operation_advice="持有",
        success=True,
        dashboard={"core_conclusion": {"one_sentence": "可持有"}},
    )
    mock_cls.return_value = mock_analyzer

    md, source, active, result = run_cs_item_llm_analysis(ctx, skills=["bull_trend"], analyzer=mock_analyzer)
    assert source == "llm"
    assert active == ("bull_trend",)
    assert result is not None
    assert result.success is True
    mock_analyzer.analyze.assert_called_once()
    call_ctx = mock_analyzer.analyze.call_args[0][0]
    assert call_ctx["asset_type"] == "cs_item"
    assert "## 核心结论" in md


def test_build_cs_report_payload_from_llm_result():
    ctx = _minimal_ctx()
    ctx.snapshot["container"] = [{"name": "手套武器箱", "id": 123, "price": 2.5}]
    result = AnalysisResult(
        code="cs:1",
        name="测试刀",
        sentiment_score=72,
        trend_prediction="震荡偏多",
        operation_advice="持有",
        success=True,
        dashboard={
            "core_conclusion": {"one_sentence": "可持有观望"},
            "battle_plan": {
                "sniper_points": {
                    "ideal_buy": "900 附近",
                    "stop_loss": "跌破 850",
                }
            },
        },
    )
    payload = build_cs_report_payload(ctx, result)
    assert payload["summary"]["analysis_summary"] == "可持有观望"
    assert payload["summary"]["operation_advice"] == "持有"
    assert payload["strategy"]["ideal_buy"] == "900 附近"
    assert payload["belong_boards"][0]["name"] == "手套武器箱"
    assert payload["diagnostics"]["status"] in {"normal", "degraded"}
    assert "csqaq_api" in payload["diagnostics"]["components"]
