# -*- coding: utf-8 -*-
"""Extract item keywords and score event-intel relevance for a CS skin."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Literal, Optional, Tuple

logger = logging.getLogger(__name__)

RelevanceTier = Literal["direct", "case", "market", "drop"]

_WEAR_ZH = ("崭新出厂", "略有磨损", "久经沙场", "破损不堪", "战痕累累")
_WEAR_EN = ("Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred")
_MARKET_TERMS = (
    "cs2",
    "csgo",
    "counter-strike",
    "counter strike",
    "skin",
    "skins",
    "sticker",
    "stickers",
    "capsule",
    "case",
    "major",
    "iem",
    "cologne",
    "shanghai",
    "buff",
    "steam market",
    "饰品",
    "贴纸",
    "武器箱",
    "新箱",
    "开箱",
    "valve",
    "update",
    "patch",
    "collection",
)
_HLTV_MARKET_HINTS = _MARKET_TERMS + (
    "tournament",
    "playoffs",
    "stage 1",
    "stage 2",
    "economy",
    "drop pool",
)
# Common CN -> EN weapon case aliases for search queries.
_CASE_EN_ALIASES: dict[str, str] = {
    "手套武器箱": "glove case",
    "伽玛武器箱": "gamma case",
    "光谱武器箱": "spectrum case",
    "裂空武器箱": "fracture case",
    "反冲武器箱": "recoil case",
    "变革武器箱": "revolution case",
    "千瓦武器箱": "kilowatt case",
}


@dataclass(frozen=True)
class CSItemIntelKeywords:
    """Keywords derived from the analyzed item."""

    direct: FrozenSet[str]
    cases: FrozenSet[str]
    market: FrozenSet[str]
    case_labels: Tuple[str, ...] = ()


def _normalize_token(value: str) -> str:
    return " ".join((value or "").lower().split())


def _split_item_name(item_name: str) -> Tuple[str, str]:
    raw = (item_name or "").strip()
    if "|" not in raw:
        return raw, ""
    left, right = raw.split("|", 1)
    skin = right.strip()
    for wear in _WEAR_ZH:
        skin = skin.replace(f"({wear})", "").replace(wear, "").strip()
    skin = skin.replace("(", " ").replace(")", " ").strip()
    return left.strip(), skin


def _split_market_hash_name(market_hash_name: str) -> Tuple[str, str]:
    raw = (market_hash_name or "").strip()
    if "|" not in raw:
        return raw, ""
    weapon, rest = raw.split("|", 1)
    skin = rest.strip()
    for wear in _WEAR_EN:
        skin = skin.replace(f"({wear})", "").replace(wear, "").strip()
    skin = skin.replace("(", " ").replace(")", " ").strip()
    return weapon.strip(), skin


def _expand_case_aliases(case_name: str) -> set[str]:
    raw = (case_name or "").strip()
    if not raw:
        return set()
    terms = {_normalize_token(raw)}
    if raw.endswith("武器箱"):
        stem = raw[: -len("武器箱")].strip()
        if stem:
            terms.add(_normalize_token(f"{stem}武器箱"))
            terms.add(_normalize_token(f"{stem} case"))
            terms.add(_normalize_token(f"{stem} weapon case"))
    mapped = _CASE_EN_ALIASES.get(raw)
    if mapped:
        terms.add(_normalize_token(mapped))
    return terms


def resolve_item_containers(good_id: int) -> List[str]:
    """Read weapon case names from CSQAQ item detail (``container`` field)."""
    try:
        from market_provider.csqaq.client import CSQAQClient

        detail = CSQAQClient().get_item_good(int(good_id))
        containers = detail.get("container") or []
        names: List[str] = []
        for entry in containers:
            if isinstance(entry, dict):
                name = str(entry.get("name") or "").strip()
                if name:
                    names.append(name)
        return names
    except Exception as exc:
        logger.warning("无法读取 good_id=%s 所属武器箱: %s", good_id, exc)
        return []


def build_case_search_query(case_labels: Iterable[str]) -> str:
    parts: List[str] = []
    for label in case_labels:
        label = label.strip()
        if not label:
            continue
        parts.append(label)
        parts.extend(_expand_case_aliases(label))
        parts.append(f"{label} CS2")
    if not parts:
        return ""
    unique = []
    seen = set()
    for part in parts:
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(part)
    return " OR ".join(unique[:8])


def build_cs_item_intel_keywords(
    *,
    item_name: str,
    market_hash_name: str,
    good_id: Optional[int] = None,
    container_names: Optional[List[str]] = None,
) -> CSItemIntelKeywords:
    direct: set[str] = set()
    weapon_zh, skin_zh = _split_item_name(item_name)
    weapon_en, skin_en = _split_market_hash_name(market_hash_name)

    for token in (weapon_zh, skin_zh, weapon_en, skin_en):
        norm = _normalize_token(token)
        if len(norm) >= 2:
            direct.add(norm)
    for part in re.split(r"[\s|/()]+", item_name or ""):
        part = part.strip()
        if len(part) >= 2 and part not in _WEAR_ZH:
            direct.add(_normalize_token(part))

    if good_id is not None:
        direct.add(str(good_id))

    cases: set[str] = set()
    labels: List[str] = []
    for name in container_names or []:
        name = str(name).strip()
        if not name:
            continue
        labels.append(name)
        cases.update(_expand_case_aliases(name))

    market = set(_normalize_token(t) for t in _MARKET_TERMS)
    return CSItemIntelKeywords(
        direct=frozenset(direct),
        cases=frozenset(cases),
        market=frozenset(market),
        case_labels=tuple(labels),
    )


def _blob(title: str, snippet: str) -> str:
    return _normalize_token(f"{title} {snippet}")


def _contains_any(blob: str, terms: Iterable[str]) -> bool:
    return any(term and term in blob for term in terms)


def score_event_relevance(
    *,
    title: str,
    snippet: str,
    dimension: str,
    keywords: CSItemIntelKeywords,
) -> RelevanceTier:
    blob = _blob(title, snippet)

    if _contains_any(blob, keywords.direct):
        return "direct"

    if keywords.cases and _contains_any(blob, keywords.cases):
        return "case"

    if dimension == "case_focus":
        return "case" if keywords.case_labels else "drop"

    if dimension in ("official_crawl", "official_update", "new_case", "major_sticker"):
        return "market"

    if dimension in ("cs_market", "tieba"):
        if _contains_any(blob, keywords.market):
            return "market"
        return "drop"

    if dimension in ("hltv", "hltv_crawl"):
        if _contains_any(blob, _HLTV_MARKET_HINTS):
            return "market"
        return "drop"

    if _contains_any(blob, keywords.market):
        return "market"
    return "drop"
