# -*- coding: utf-8 -*-
"""Resolution failure direct reply."""

from __future__ import annotations

from src.services.cs_chat_pipeline import ChatPipelineResult, try_build_resolution_failure_reply
from src.services.cs_entity_resolver import ResolvedEntity


def test_resolution_failure_reply():
    pipeline = ChatPipelineResult(
        scope="general",
        intent="general",
        entity=ResolvedEntity(item_query="M4A1闪回"),
        narrator_payload={
            "mode": "general",
            "entity": {"item_query": "M4A1闪回", "resolution_failed": True, "catalog_candidates": []},
        },
    )
    reply = try_build_resolution_failure_reply(pipeline)
    assert reply is not None
    assert "M4A1闪回" in reply
    assert "401" in reply
    assert "sync_cs_item_catalog" in reply
    assert "首页" not in reply or "无需手动去首页" in reply
