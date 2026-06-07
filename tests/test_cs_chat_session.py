# -*- coding: utf-8 -*-
"""Tests for CS chat session memory."""

from __future__ import annotations

from src.agent.conversation import conversation_manager
from src.services.cs_chat_session import (
    clear_current_item,
    get_current_item,
    get_last_intent,
    set_current_item,
    set_last_intent,
)


def test_session_item_binding():
    sid = "cs_test_session_memory"
    conversation_manager.clear(sid)
    set_current_item(sid, good_id=769, item_name="法玛斯 | 机械工业 (崭新出厂)")
    item = get_current_item(sid)
    assert item is not None
    assert item["good_id"] == 769
    assert "法玛斯" in item["item_name"]
    clear_current_item(sid)
    assert get_current_item(sid) is None


def test_session_intent_memory():
    sid = "cs_test_intent_memory"
    conversation_manager.clear(sid)
    set_last_intent(sid, "manipulation")
    assert get_last_intent(sid) == "manipulation"
