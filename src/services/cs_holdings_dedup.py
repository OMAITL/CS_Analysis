# -*- coding: utf-8 -*-
"""Dedup key helpers for CS holdings import."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Optional

_WEAR_ALIASES = {
    "fn": "崭新出厂",
    "mw": "略有磨损",
    "ft": "久经沙场",
    "ww": "破损不堪",
    "bs": "战痕累累",
    "factory new": "崭新出厂",
    "minimal wear": "略有磨损",
    "field-tested": "久经沙场",
    "well-worn": "破损不堪",
    "battle-scarred": "战痕累累",
}


def normalize_wear(value: Optional[str]) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    if text in _WEAR_ALIASES:
        return _WEAR_ALIASES[text]
    for canonical in _WEAR_ALIASES.values():
        if text == canonical.lower():
            return canonical
    return (value or "").strip()


def normalize_item_name(value: Optional[str]) -> str:
    text = (value or "").strip().lower()
    text = text.replace("｜", "|")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[（(].*?[)）]", "", text)
    return text.strip()


def float_bucket(float_value: Optional[float]) -> str:
    if float_value is None:
        return ""
    try:
        return f"{round(float(float_value), 2):.2f}"
    except (TypeError, ValueError):
        return ""


def compute_dedup_key(
    *,
    item_name: str,
    wear: str = "",
    float_value: Optional[float] = None,
    platform: str = "yyyp",
) -> str:
    parts = "|".join(
        [
            normalize_item_name(item_name),
            normalize_wear(wear),
            float_bucket(float_value),
            (platform or "yyyp").strip().lower(),
        ]
    )
    return hashlib.sha256(parts.encode("utf-8")).hexdigest()[:32]


def attach_dedup_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(payload)
    payload["dedup_key"] = compute_dedup_key(
        item_name=str(payload.get("item_name") or ""),
        wear=str(payload.get("wear") or ""),
        float_value=payload.get("float_value"),
        platform=str(payload.get("platform") or "yyyp"),
    )
    return payload
