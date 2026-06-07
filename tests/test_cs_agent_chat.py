# -*- coding: utf-8 -*-
"""Tests for CS agent tools and chat service wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.agent.tools.cs_tools import _handle_analyze_cs_item, _handle_search_cs_item
from src.services.cs_chat_service import CSChatService


@patch("src.services.cs_item_resolve_service.resolve_good_id_from_queries")
def test_search_cs_item_returns_candidates(mock_resolve):
    mock_resolve.return_value = (
        1239,
        "M4A1-S | 闪回 (久经沙场)",
        "M4A1-S | Flashback (Field-Tested)",
        1.0,
        "闪回",
        [{"good_id": 1239, "name": "M4A1-S | 闪回 (久经沙场)", "score": 1.0}],
    )
    payload = _handle_search_cs_item("M4A1 闪回")
    assert payload["status"] == "ok"
    assert payload["best_match"]["good_id"] == 1239
    assert payload["items"]


@patch("src.services.cs_item_data_provider.ItemDataProvider")
def test_analyze_cs_item_returns_trend(mock_provider_cls):
    mock_provider_cls.return_value.fetch_with_backfill.return_value = MagicMock(
        good_id=1239,
        error=None,
        trend={"signal_score": 57, "buy_signal": "持有", "rsi_12": 78.0},
        item_info={"name": "M4A1-S | 闪回 (久经沙场)", "yyyp_sell_price": 47.92},
        price_history=[{"date": "2026-06-01", "close": 47.0, "volume": 12}],
        meta={"data_quality": "full"},
    )
    payload = _handle_analyze_cs_item(1239)
    assert payload["status"] == "ok"
    assert payload["good_id"] == 1239
    assert payload["trend"]["signal_score"] == 57
    assert payload["recent_daily_bars"]


@patch("src.agent.cs_factory.build_cs_agent_executor")
def test_cs_chat_service_uses_agent_executor(mock_build):
    mock_executor = MagicMock()
    mock_executor.chat.return_value = MagicMock(success=True, content="测试回答", error=None)
    mock_build.return_value = mock_executor

    result = CSChatService().chat(message="M4A1 闪回适合卖吗", session_id="cs_test_agent")

    assert result.success is True
    assert result.content == "测试回答"
    mock_executor.chat.assert_called_once()
    call_kw = mock_executor.chat.call_args.kwargs
    assert call_kw["message"] == "M4A1 闪回适合卖吗"
    assert call_kw["session_id"] == "cs_test_agent"
