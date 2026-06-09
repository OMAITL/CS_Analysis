# -*- coding: utf-8 -*-
"""Resolve CS chat answer scope — delegates to cs_chat_pipeline where possible."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Literal, Optional

from src.services.cs_chat_pipeline import resolve_pipeline_scope
from src.services.cs_chat_session import get_current_item, get_last_intent
from src.services.cs_entity_resolver import resolve_entities

logger = logging.getLogger(__name__)

ChatAnswerScope = Literal["market", "portfolio", "single_item", "general"]


def resolve_chat_scope(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    explicit_scope: Optional[str] = None,
    session_id: Optional[str] = None,
) -> ChatAnswerScope:
    """Backward-compatible scope resolver using entity + session memory."""
    ctx = dict(context or {})
    session_item = get_current_item(session_id) if session_id else None
    entity = resolve_entities(
        message,
        request_context=ctx,
        session_item=session_item,
        last_intent=get_last_intent(session_id) if session_id else None,
    )
    return resolve_pipeline_scope(
        message,
        entity,
        explicit_scope=explicit_scope or str(ctx.get("scope") or "") or None,
        session_item=session_item,
    )


def build_scope_context_block(
    message: str,
    context: Optional[Dict[str, Any]],
    *,
    fetch_item_context: Any,
    session_id: Optional[str] = None,
) -> str:
    """Legacy hook — prefer cs_chat_pipeline.build_narrator_context_block."""
    from src.services.cs_chat_pipeline import build_narrator_context_block, run_cs_chat_pipeline

    pipeline = run_cs_chat_pipeline(
        session_id=session_id or "legacy",
        message=message,
        request_context=context,
    )
    return build_narrator_context_block(pipeline)


def _fetch_market_context(message: str = "") -> Dict[str, Any]:
    payload: Dict[str, Any] = {"scope": "market"}
    try:
        from src.services.cs_skill_prompt import fetch_cs_index_summary

        index_summary = fetch_cs_index_summary()
        if index_summary:
            payload["index_summary"] = index_summary
    except Exception as exc:
        logger.debug("CS chat market index summary failed: %s", exc)

    try:
        from market_provider.csqaq.client import CSQAQClient
        from src.services.cs_skill_prompt import compact_sub_index_row

        client = CSQAQClient()
        indexes = client.list_sub_indexes()
        compact = []
        for row in indexes[:12]:
            if not isinstance(row, dict):
                continue
            normalized = compact_sub_index_row(row)
            compact.append(
                {
                    "id": normalized.get("id"),
                    "name": normalized.get("name"),
                    "price": normalized.get("market_index") or normalized.get("close"),
                    "change": normalized.get("chg_rate") or normalized.get("change_pct"),
                    "chg_num": normalized.get("chg_num"),
                }
            )
        if compact:
            payload["sub_indexes"] = compact
    except Exception as exc:
        logger.debug("CS chat sub_indexes failed: %s", exc)
        payload["sub_indexes_error"] = str(exc)

    try:
        from src.services.cs_market_scan_service import scan_market_watchlist

        scan = scan_market_watchlist(message)
        payload["market_intent"] = scan.get("intent")
        payload["watchlist"] = scan.get("watchlist") or []
        payload["authorized_items"] = scan.get("authorized_items") or []
        payload["category_examples"] = scan.get("category_examples") or []
        if scan.get("watchlist_table_markdown"):
            payload["watchlist_table_markdown"] = scan["watchlist_table_markdown"]
        payload["scan_meta"] = {
            "method": scan.get("scan_method"),
            "pool_size": scan.get("pool_size"),
            "analyzed_count": scan.get("analyzed_count"),
        }
        if scan.get("note"):
            payload["scan_note"] = scan["note"]
    except Exception as exc:
        logger.warning("CS chat market watchlist scan failed: %s", exc)
        payload["watchlist_error"] = str(exc)

    payload["note"] = (
        "回答结构要求：1) **复制** `watchlist_table_markdown` 预生成表；"
        "2) 只能引用 `authorized_items`；3) 简短框架；4) 声明抽样扫描非穷尽。"
    )
    return payload


def _fetch_portfolio_context() -> Dict[str, Any]:
    try:
        from src.services.cs_holdings_service import CSHoldingsService

        snapshot = CSHoldingsService().get_snapshot(refresh_prices=False)
        items = list(snapshot.get("items") or [])
        return {
            "scope": "portfolio",
            "summary": snapshot.get("summary") or {},
            "items": items[:20],
            "truncated": len(items) > 20,
            "note": "价格为库内缓存，未逐件刷新；单品技术诊断需 good_id。",
        }
    except Exception as exc:
        logger.warning("CS chat portfolio context failed: %s", exc)
        return {"scope": "portfolio", "error": str(exc), "items": []}
