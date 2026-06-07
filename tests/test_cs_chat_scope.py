# -*- coding: utf-8 -*-
"""Tests for CS chat answer scope resolution."""

from __future__ import annotations

from src.agent.conversation import conversation_manager
from src.services.cs_chat_scope import resolve_chat_scope
from src.services.cs_chat_session import set_current_item


def test_market_scope_for_which_items_question():
    scope = resolve_chat_scope(
        "哪些饰品可能有人在做盘？怎么识别？",
        {"good_id": 769, "item_name": "法玛斯 | 机械工业 (崭新出厂)"},
    )
    assert scope == "market"


def test_portfolio_scope_for_holdings_question():
    scope = resolve_chat_scope("我持有的饰品在高位要不要出货？")
    assert scope == "portfolio"


def test_single_item_scope_with_linked_context():
    scope = resolve_chat_scope(
        "当前在高位要不要减仓？",
        {"good_id": 769, "item_name": "法玛斯 | 机械工业 (崭新出厂)"},
    )
    assert scope == "single_item"


def test_explicit_scope_from_context():
    scope = resolve_chat_scope(
        "随便问问",
        {"scope": "market", "good_id": 1, "item_name": "X"},
        explicit_scope="market",
    )
    assert scope == "market"


def test_general_scope_without_markers():
    scope = resolve_chat_scope("BUFF 和悠悠有价差，套利要注意什么？")
    assert scope == "general"


def test_followup_manipulation_question_is_market_scope():
    scope = resolve_chat_scope("还有别的可能做盘目标吗")
    assert scope == "market"


def test_followup_explain_uses_session_item():
    sid = "cs_test_scope_followup"
    conversation_manager.clear(sid)
    set_current_item(sid, good_id=769, item_name="法玛斯 | 机械工业 (崭新出厂)")
    scope = resolve_chat_scope(
        "那你怎么知道有人做盘？",
        session_id=sid,
    )
    assert scope == "single_item"


def test_single_item_scope_for_high_position_sell_question():
    scope = resolve_chat_scope(
        "法玛斯 | 机械工业 崭新出厂，我觉得价格已处高位，有些犹豫要不要卖掉一部分还是继续等下一波高点",
        {"good_id": 769, "item_name": "法玛斯 | 机械工业 (崭新出厂)"},
    )
    assert scope == "single_item"
