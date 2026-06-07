# -*- coding: utf-8 -*-
"""Tests for CS entity resolver."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.services.cs_entity_resolver import (
    INTENT_MANIPULATION,
    INTENT_MARKET_SCAN,
    detect_intent,
    resolve_entities,
)


def test_detect_manipulation_intent():
    assert detect_intent("法玛斯机械工业是不是有人在做盘？") == INTENT_MANIPULATION


def test_detect_market_scan_intent():
    assert detect_intent("还有别的可能做盘目标吗") == INTENT_MARKET_SCAN


def test_detect_explain_follow_up_as_manipulation():
    assert detect_intent("那你怎么知道有人做盘？", last_intent=INTENT_MANIPULATION) == INTENT_MANIPULATION


@patch("src.repositories.cs_item_catalog_repo.CSItemCatalogRepository")
def test_resolve_item_from_catalog(mock_repo_cls):
    row = MagicMock()
    row.good_id = 769
    row.name = "法玛斯 | 机械工业 (崭新出厂)"
    row.market_hash_name = "FAMAS | Mecha Industries (Factory New)"
    mock_repo_cls.return_value.search_items.return_value = ([row], 1)

    entity = resolve_entities("法玛斯机械工业是不是有人在做盘？")

    assert entity.good_id == 769
    assert entity.intent == INTENT_MANIPULATION
    assert entity.source in {"catalog", "hybrid"}


def test_resolve_session_memory_when_no_item_in_message():
    entity = resolve_entities(
        "那你怎么知道有人做盘？",
        session_item={"good_id": 769, "item_name": "法玛斯 | 机械工业 (崭新出厂)"},
        last_intent=INTENT_MANIPULATION,
    )
    assert entity.good_id == 769
    assert entity.source == "session_memory"


def test_request_context_overrides_session():
    entity = resolve_entities(
        "那你怎么知道有人做盘？",
        request_context={"good_id": 100, "item_name": "X"},
        session_item={"good_id": 769, "item_name": "法玛斯"},
    )
    assert entity.good_id == 100
    assert entity.source == "request_context"


def test_request_context_ignored_when_message_names_new_item():
    from unittest.mock import patch

    row = MagicMock()
    row.good_id = 1239
    row.name = "M4A1-S | 闪回 (久经沙场)"
    row.market_hash_name = "M4A1-S | Flashback (Field-Tested)"
    with patch("src.repositories.cs_item_catalog_repo.CSItemCatalogRepository") as mock_repo_cls:
        mock_repo_cls.return_value.search_items.return_value = ([row], 1)
        entity = resolve_entities(
            "M4A1 闪回现在适合买吗",
            request_context={"good_id": 769, "item_name": "法玛斯 | 机械工业"},
            session_item={"good_id": 769, "item_name": "法玛斯 | 机械工业"},
        )
    assert entity.good_id == 1239
    assert entity.source in {"catalog", "hybrid"}


def test_extract_compact_weapon_skin():
    from src.services.cs_entity_resolver import _extract_item_query_candidates

    cands = _extract_item_query_candidates("这个M4A1-S闪回是不是有人做盘")
    joined = " ".join(cands)
    assert "M4A1-S" in joined
    assert "闪回" in joined


def test_extract_knife_skin():
    from src.services.cs_entity_resolver import _extract_item_query_candidates

    cands = _extract_item_query_candidates("帮我看看蝴蝶刀多普勒")
    assert any("蝴蝶刀" in c and "多普勒" in c for c in cands)
