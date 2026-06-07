# -*- coding: utf-8 -*-
"""Tests for CS chat pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.agent.conversation import conversation_manager
from src.services.cs_chat_pipeline import resolve_pipeline_scope, run_cs_chat_pipeline
from src.services.cs_chat_session import set_current_item
from src.services.cs_entity_resolver import ResolvedEntity, INTENT_MANIPULATION, INTENT_MARKET_SCAN


def test_follow_up_manipulation_uses_session_item_not_market():
    sid = "cs_test_pipeline_followup"
    conversation_manager.clear(sid)
    set_current_item(sid, good_id=769, item_name="法玛斯 | 机械工业 (崭新出厂)")

    entity = ResolvedEntity(
        good_id=769,
        item_name="法玛斯 | 机械工业 (崭新出厂)",
        intent=INTENT_MANIPULATION,
        source="session_memory",
        confidence=0.9,
    )
    scope = resolve_pipeline_scope(
        "那你怎么知道有人做盘？",
        entity,
        session_item={"good_id": 769, "item_name": "法玛斯 | 机械工业 (崭新出厂)"},
    )
    assert scope == "single_item"


def test_explicit_market_scan_stays_market():
    entity = ResolvedEntity(intent=INTENT_MARKET_SCAN, source="none")
    scope = resolve_pipeline_scope("还有别的可能做盘目标吗", entity)
    assert scope == "market"


@patch("src.services.cs_chat_pipeline.ItemDataProvider")
@patch("src.services.cs_chat_pipeline.CSSkillEngine")
def test_pipeline_binds_session_and_runs_skills(mock_engine_cls, mock_provider_cls):
    sid = "cs_test_pipeline_run"
    conversation_manager.clear(sid)

    mock_provider_cls.return_value.fetch_with_backfill.return_value = MagicMock(
        error=None,
        trend={"signal_score": 58},
        item_info={"name": "法玛斯 | 机械工业 (崭新出厂)"},
        to_dict=lambda: {"trend": {"signal_score": 58}},
    )
    mock_engine_cls.return_value.run.return_value = MagicMock(
        to_dict=lambda: {"manipulation": {"score": 40, "probability": "中", "signals": ["test"]}}
    )

    with patch("src.repositories.cs_item_catalog_repo.CSItemCatalogRepository") as mock_repo:
        row = MagicMock()
        row.good_id = 769
        row.name = "法玛斯 | 机械工业 (崭新出厂)"
        row.market_hash_name = "FAMAS | Mecha Industries (Factory New)"
        mock_repo.return_value.search_items.return_value = ([row], 1)

        result = run_cs_chat_pipeline(
            session_id=sid,
            message="法玛斯机械工业是不是有人在做盘？",
        )

    assert result.scope == "single_item"
    assert result.entity.good_id == 769
    mock_provider_cls.return_value.fetch_with_backfill.assert_called_once()
    mock_engine_cls.return_value.run.assert_called_once()
    from src.services.cs_chat_session import get_current_item

    assert get_current_item(sid)["good_id"] == 769
