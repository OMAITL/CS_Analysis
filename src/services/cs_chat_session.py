# -*- coding: utf-8 -*-
"""Session memory for CS chat: bind current_item across turns."""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.agent.conversation import conversation_manager

SESSION_ITEM_KEY = "cs_current_item"
SESSION_INTENT_KEY = "cs_last_intent"
SESSION_PENDING_QUERY_KEY = "cs_pending_item_query"


def get_pending_item_query(session_id: str) -> str:
    value = _session(session_id).context.get(SESSION_PENDING_QUERY_KEY)
    return str(value).strip() if value else ""


def set_pending_item_query(session_id: str, query: str) -> None:
    text = (query or "").strip()
    if not text:
        _session(session_id).context.pop(SESSION_PENDING_QUERY_KEY, None)
        return
    _session(session_id).update_context(SESSION_PENDING_QUERY_KEY, text)


def clear_pending_item_query(session_id: str) -> None:
    _session(session_id).context.pop(SESSION_PENDING_QUERY_KEY, None)


def _session(session_id: str):
    return conversation_manager.get_or_create(session_id)


def get_current_item(session_id: str) -> Optional[Dict[str, Any]]:
    """Return bound item for this chat session, if any."""
    ctx = _session(session_id).context
    item = ctx.get(SESSION_ITEM_KEY)
    if not isinstance(item, dict):
        return None
    good_id = item.get("good_id")
    if good_id is None:
        return None
    try:
        gid = int(good_id)
    except (TypeError, ValueError):
        return None
    return {
        "good_id": gid,
        "item_name": str(item.get("item_name") or item.get("name") or ""),
        "market_hash_name": str(item.get("market_hash_name") or ""),
        "platform": item.get("platform"),
    }


def set_current_item(
    session_id: str,
    *,
    good_id: int,
    item_name: str = "",
    market_hash_name: str = "",
    platform: Optional[str] = None,
) -> None:
    """Bind good_id to session for follow-up turns without item name."""
    _session(session_id).update_context(
        SESSION_ITEM_KEY,
        {
            "good_id": int(good_id),
            "item_name": (item_name or "").strip(),
            "market_hash_name": (market_hash_name or "").strip(),
            "platform": platform,
        },
    )


def clear_current_item(session_id: str) -> None:
    session = _session(session_id)
    session.context.pop(SESSION_ITEM_KEY, None)


def get_last_intent(session_id: str) -> Optional[str]:
    value = _session(session_id).context.get(SESSION_INTENT_KEY)
    return str(value).strip() if value else None


def set_last_intent(session_id: str, intent: str) -> None:
    _session(session_id).update_context(SESSION_INTENT_KEY, (intent or "").strip())
