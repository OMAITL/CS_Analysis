# -*- coding: utf-8 -*-
"""Persist CS chat session ↔ item bindings for Web UI."""

from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_BINDINGS_PATH = Path("data/cs_chat_session_bindings.json")
_lock = threading.Lock()


def _load_all() -> Dict[str, Dict[str, Any]]:
    with _lock:
        if not _BINDINGS_PATH.is_file():
            return {}
        try:
            raw = json.loads(_BINDINGS_PATH.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except Exception as exc:
            logger.debug("Failed to load CS chat session bindings: %s", exc)
            return {}


def _save_all(data: Dict[str, Dict[str, Any]]) -> None:
    with _lock:
        _BINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _BINDINGS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def binding_from_context(context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not context:
        return None
    item_name = str(context.get("item_name") or "").strip()
    good_id = context.get("good_id")
    if not item_name and good_id is None:
        return None
    binding: Dict[str, Any] = {}
    if good_id is not None:
        try:
            binding["good_id"] = int(good_id)
        except (TypeError, ValueError):
            pass
    if item_name:
        binding["item_name"] = item_name
    platform = context.get("platform")
    if platform:
        binding["platform"] = str(platform)
    summary = context.get("previous_analysis_summary")
    if summary:
        binding["previous_analysis_summary"] = str(summary)
    return binding or None


def infer_item_name_from_text(text: str) -> Optional[str]:
    if not text or "|" not in text:
        return None
    patterns = (
        r"(?:基于|针对)\s*([^,\n（(]+(?:\([^)]+\))?)",
        r"(AK[-\s]?47|AWP|M4A1[^\s|]*|Glock-18|USP[^\s|]*|[^|\n]{2,24})\s*\|\s*[^\n,（(]+(?:\([^)]+\))?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = match.group(1).strip()
        if "|" in candidate and len(candidate) <= 120:
            return candidate
    return None


def infer_binding_from_messages(messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for msg in reversed(messages):
        if (msg.get("role") or "").lower() != "assistant":
            continue
        item_name = infer_item_name_from_text(str(msg.get("content") or ""))
        if item_name:
            return {"item_name": item_name}
    return None


def get_session_binding(session_id: str) -> Optional[Dict[str, Any]]:
    data = _load_all()
    row = data.get(session_id)
    return dict(row) if isinstance(row, dict) else None


def save_session_binding(session_id: str, binding: Optional[Dict[str, Any]]) -> None:
    sid = (session_id or "").strip()
    if not sid:
        return
    data = _load_all()
    if not binding:
        if sid in data:
            del data[sid]
            _save_all(data)
        return
    cleaned = binding_from_context(binding) or {}
    if not cleaned.get("item_name") and cleaned.get("good_id") is None:
        return
    data[sid] = cleaned
    _save_all(data)


def resolve_session_binding(
    session_id: str,
    messages: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    binding = get_session_binding(session_id)
    if binding:
        return binding
    if not messages:
        return None
    inferred = infer_binding_from_messages(messages)
    if inferred:
        save_session_binding(session_id, inferred)
    return inferred


def delete_session_binding(session_id: str) -> None:
    save_session_binding(session_id, None)
