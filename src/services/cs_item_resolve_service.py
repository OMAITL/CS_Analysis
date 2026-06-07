# -*- coding: utf-8 -*-
"""Resolve CS item good_id from local catalog with CSQAQ hybrid fallback."""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Common CS weapon tokens for query reordering (skin + weapon messages).
_WEAPON_TOKENS = (
    "M4A1-S",
    "M4A1",
    "M4A4",
    "AK-47",
    "AWP",
    "USP-S",
    "Glock-18",
    "Desert Eagle",
    "法玛斯",
    "加利尔",
    "SG 553",
    "AUG",
    "SSG 08",
    "SCAR-20",
    "G3SG1",
    "MAC-10",
    "MP9",
    "MP7",
    "UMP-45",
    "P90",
    "PP-Bizon",
    "Nova",
    "XM1014",
    "MAG-7",
    "Sawed-Off",
    "Negev",
    "M249",
    "蝴蝶刀",
    "爪子刀",
    "熊刀",
    "折叠刀",
    "猎杀者匕首",
    "弯刀",
    "短剑",
    "锯齿爪刀",
    "流浪者匕首",
    "骷髅匕首",
    "系绳匕首",
    "求生匕首",
    "暗影双匕",
    "刺刀",
    "鲍伊猎刀",
    "穿肠刀",
    "运动手套",
    "摩托手套",
    "专业手套",
    "驾驶手套",
    "血猎手套",
    "裹手",
    "九头蛇手套",
    "狂牙手套",
    "Sport Gloves",
    "Moto Gloves",
    "Specialist Gloves",
    "Driver Gloves",
    "Hand Wraps",
    "Bloodhound Gloves",
    "Hydra Gloves",
    "Broken Fang Gloves",
)
_WEAR_SUFFIX_RE = re.compile(r"\s*[（(][^)）]*[)）]\s*$")
_STAR_PREFIX_RE = re.compile(r"^[★*\s]+")
_WEAPON_PATTERN = "|".join(re.escape(w) for w in sorted(_WEAPON_TOKENS, key=len, reverse=True))
_SKIN_WEAPON_RE = re.compile(
    rf"^([\u4e00-\u9fffA-Za-z0-9\-]+)\s+({_WEAPON_PATTERN})\s*$",
    re.IGNORECASE,
)
_WEAPON_SKIN_RE = re.compile(
    rf"^({_WEAPON_PATTERN})\s+([\u4e00-\u9fffA-Za-z0-9\-]+)\s*$",
    re.IGNORECASE,
)
_COMPACT_WEAPON_SKIN_RE = re.compile(
    rf"^({_WEAPON_PATTERN})([\u4e00-\u9fffA-Za-z0-9\-]+)$",
    re.IGNORECASE,
)
_COMPACT_SKIN_WEAPON_RE = re.compile(
    rf"^([\u4e00-\u9fffA-Za-z0-9\-]+)({_WEAPON_PATTERN})$",
    re.IGNORECASE,
)


def _expand_weapon_skin_variants(weapon: str, skin: str, *, add: Callable[[str], None]) -> None:
    weapon = weapon.strip()
    skin = skin.strip()
    add(f"{weapon} {skin}")
    add(f"{weapon} | {skin}")
    add(f"{weapon}{skin}")
    if len(skin) >= 2:
        add(skin)
    if weapon.upper().startswith("M4A1") and not weapon.upper().endswith("-S"):
        add(f"M4A1-S | {skin}")
        add(f"M4A1-S {skin}")


def strip_wear_suffix(text: str) -> str:
    return _WEAR_SUFFIX_RE.sub("", (text or "").strip()).strip()


def _normalize_match_compact(text: str) -> str:
    value = (text or "").lower()
    value = value.replace("★", "").replace("（", "(").replace("）", ")")
    value = re.sub(r"[|｜/\s]", "", value)
    value = re.sub(r"\([^)]*\)", "", value)
    return value


def _expand_pipe_delimited_item(raw: str, *, add: Callable[[str], None]) -> None:
    """Expand ★手套 | 皮肤、武器 | 皮肤 等常见中文饰品名。"""
    base = strip_wear_suffix(raw)
    if not base:
        return
    add(base)
    no_star = _STAR_PREFIX_RE.sub("", base).strip()
    if no_star and no_star != base:
        add(no_star)

    parts = [p.strip() for p in re.split(r"[|｜]", no_star or base) if p.strip()]
    if len(parts) < 2:
        return

    left = _STAR_PREFIX_RE.sub("", parts[0]).strip()
    right = strip_wear_suffix(parts[1])
    if not left or not right:
        return

    for prefix in ("", "★ ", "★"):
        weapon = f"{prefix}{left}".strip()
        add(f"{weapon} | {right}")
        add(f"{weapon}（★） | {right}")
        add(f"{weapon}{right}")
    add(right)
    add(left)


def expand_item_search_queries(query: str) -> List[str]:
    """Expand one user fragment into catalog-friendly search variants."""
    raw = (query or "").strip()
    if not raw:
        return []

    variants: List[str] = []
    seen: set[str] = set()

    def _add(value: str) -> None:
        text = (value or "").strip()
        if len(text) < 2 or text in seen:
            return
        seen.add(text)
        variants.append(text)

    _add(raw)
    _expand_pipe_delimited_item(raw, add=_add)
    stripped = strip_wear_suffix(raw)
    if stripped and stripped != raw:
        _add(stripped)
        _expand_pipe_delimited_item(stripped, add=_add)

    skin_weapon = _SKIN_WEAPON_RE.match(raw)
    if skin_weapon:
        skin, weapon = skin_weapon.group(1).strip(), skin_weapon.group(2).strip()
        _expand_weapon_skin_variants(weapon, skin, add=_add)

    weapon_skin = _WEAPON_SKIN_RE.match(raw)
    if weapon_skin:
        weapon, skin = weapon_skin.group(1).strip(), weapon_skin.group(2).strip()
        _expand_weapon_skin_variants(weapon, skin, add=_add)

    compact = _COMPACT_WEAPON_SKIN_RE.match(raw)
    if compact:
        weapon, skin = compact.group(1).strip(), compact.group(2).strip()
        _expand_weapon_skin_variants(weapon, skin, add=_add)

    compact_skin_weapon = _COMPACT_SKIN_WEAPON_RE.match(raw)
    if compact_skin_weapon:
        skin, weapon = compact_skin_weapon.group(1).strip(), compact_skin_weapon.group(2).strip()
        _expand_weapon_skin_variants(weapon, skin, add=_add)

    return variants


def score_item_match(query: str, row_name: str, row_mhn: str) -> float:
    q_compact = _normalize_match_compact(query)
    name_compact = _normalize_match_compact(row_name)
    mhn_compact = _normalize_match_compact(row_mhn)

    if not q_compact:
        return 0.0
    if q_compact == name_compact or q_compact == mhn_compact:
        return 1.0
    if q_compact in name_compact or name_compact.startswith(q_compact) or q_compact in mhn_compact:
        return 0.95
    if q_compact in name_compact.replace(" ", "") or q_compact in mhn_compact.replace(" ", ""):
        return 0.85

    q = query.lower().replace(" ", "").replace("|", "").replace("｜", "")
    name = (row_name or "").lower()
    mhn = (row_mhn or "").lower()
    name_compact = re.sub(r"[|｜/\s]", "", name)
    name_compact = re.sub(r"[（(].*?[)）]", "", name_compact)

    if not q:
        return 0.0
    if q == name_compact or q in name_compact or name_compact.startswith(q):
        return 1.0
    if q in name.replace(" ", "") or q in mhn.replace(" ", ""):
        return 0.85

    name_parts = [p.strip() for p in re.split(r"[|｜/]", row_name or "") if p.strip()]
    if len(name_parts) >= 2:
        joined = "".join(p.lower().replace(" ", "") for p in name_parts[:2])
        if q in joined or joined.startswith(q):
            return 0.95

    tokens = [t for t in re.split(r"[|｜/\s]+", query) if len(t) >= 2]
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t.lower() in name or t.lower() in mhn)
    return hits / len(tokens) * 0.75


def lookup_item_in_catalog(query: str) -> Tuple[Optional[int], str, str, float, List[Dict[str, Any]]]:
    if not (query or "").strip():
        return None, "", "", 0.0, []
    try:
        from src.repositories.cs_item_catalog_repo import CSItemCatalogRepository

        repo = CSItemCatalogRepository()
        rows, _total = repo.search_items(query, page_size=8)
        if not rows:
            return None, "", "", 0.0, []

        scored = [(score_item_match(query, row.name, row.market_hash_name or ""), row) for row in rows]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best = scored[0]
        candidates = [
            {
                "good_id": int(r.good_id),
                "name": r.name,
                "market_hash_name": r.market_hash_name,
                "score": round(s, 3),
            }
            for s, r in scored[:5]
        ]
        if best_score < 0.35:
            if len(rows) == 1 and len(query.strip()) >= 2:
                only = rows[0]
                return (
                    int(only.good_id),
                    str(only.name),
                    str(only.market_hash_name or only.name),
                    0.8,
                    candidates,
                )
            return None, "", "", best_score, candidates
        return (
            int(best.good_id),
            str(best.name),
            str(best.market_hash_name or best.name),
            best_score,
            candidates,
        )
    except Exception as exc:
        logger.warning("catalog lookup failed for %r: %s", query, exc)
        return None, "", "", 0.0, []


def lookup_item_hybrid(query: str) -> Tuple[Optional[int], str, str, float, List[Dict[str, Any]]]:
    """
    Local catalog first; if miss, CSQAQ search + upsert into catalog.
    """
    if not (query or "").strip():
        return None, "", "", 0.0, []

    local_gid, local_name, local_mhn, local_score, local_candidates = lookup_item_in_catalog(query)
    if local_gid is not None and local_score >= 0.35:
        return local_gid, local_name, local_mhn, local_score, local_candidates

    try:
        from src.services.cs_item_catalog_service import CSItemCatalogService

        payload = CSItemCatalogService().search_hybrid(query, page_size=8)
        items = list(payload.get("items") or [])
        if not items:
            return None, "", "", 0.0, local_candidates

        scored: List[tuple[float, Dict[str, Any]]] = []
        for item in items:
            score = score_item_match(
                query,
                str(item.get("name") or ""),
                str(item.get("market_hash_name") or ""),
            )
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best = scored[0]
        candidates = [
            {
                "good_id": int(row.get("good_id")),
                "name": row.get("name"),
                "market_hash_name": row.get("market_hash_name"),
                "score": round(s, 3),
                "source": payload.get("source"),
            }
            for s, row in scored[:5]
        ]
        if best_score < 0.3 and len(items) == 1:
            best_score = 0.75
        if best_score < 0.3 and len(items) >= 1:
            # CSQAQ 有时「M4A1 闪回」无结果但「闪回」有多条；取最高分候选
            best_score = max(best_score, float(scored[0][0]) if scored else 0.0)
            if best_score >= 0.25:
                best = scored[0][1]
                return (
                    int(best["good_id"]),
                    str(best.get("name") or ""),
                    str(best.get("market_hash_name") or best.get("name") or ""),
                    best_score,
                    candidates,
                )
        if best_score < 0.3:
            return None, "", "", best_score, candidates
        return (
            int(best["good_id"]),
            str(best.get("name") or ""),
            str(best.get("market_hash_name") or best.get("name") or ""),
            best_score,
            candidates,
        )
    except Exception as exc:
        logger.warning("hybrid item lookup failed for %r: %s", query, exc)
        err_text = str(exc).lower()
        if "401" in err_text or "unauthorized" in err_text:
            browser_candidates = _lookup_item_browser(query)
            if browser_candidates:
                best_row = browser_candidates[0]
                return (
                    int(best_row["good_id"]),
                    str(best_row.get("name") or ""),
                    str(best_row.get("market_hash_name") or best_row.get("name") or ""),
                    float(best_row.get("score") or 0.75),
                    local_candidates + browser_candidates,
                )
        return None, "", "", 0.0, local_candidates


def _lookup_item_browser(query: str) -> List[Dict[str, Any]]:
    """Resolve items via csqaq.com browser session when Open API token is unavailable."""
    if not (query or "").strip():
        return []
    try:
        from crawlers.csqaq.browser_crawler import CSQAQBrowserCrawler

        rows = CSQAQBrowserCrawler().search_goods(str(query).strip(), page_size=20)
    except Exception as exc:
        logger.warning("browser item search failed for %r: %s", query, exc)
        return []

    candidates: List[Dict[str, Any]] = []
    for row in rows:
        score = score_item_match(
            query,
            str(row.get("name") or ""),
            str(row.get("market_hash_name") or ""),
        )
        candidates.append(
            {
                "good_id": int(row["good_id"]),
                "name": row.get("name"),
                "market_hash_name": row.get("market_hash_name"),
                "score": round(max(score, 0.4), 3),
                "source": "browser",
            }
        )
    candidates.sort(key=lambda x: float(x.get("score") or 0), reverse=True)

    if candidates:
        try:
            from src.services.cs_item_catalog_service import CSItemCatalogService

            CSItemCatalogService().upsert_good_id_entries(
                [
                    {
                        "good_id": c["good_id"],
                        "name": c.get("name"),
                        "market_hash_name": c.get("market_hash_name"),
                    }
                    for c in candidates[:5]
                ]
            )
        except Exception as exc:
            logger.debug("catalog upsert from browser search failed: %s", exc)

    return candidates


def _query_specificity(query: str) -> int:
    compact = re.sub(r"\s+", "", (query or "").strip())
    bonus = 2 if "|" in query or "｜" in query else 0
    return len(compact) + bonus


def resolve_good_id_from_queries(queries: List[str]) -> Tuple[Optional[int], str, str, float, str, List[Dict[str, Any]]]:
    """
    Try multiple query variants; catalog then CSQAQ hybrid.

    Returns: good_id, name, mhn, score, best_query, candidates
    """
    best_gid: Optional[int] = None
    best_name = ""
    best_mhn = ""
    best_score = 0.0
    best_query = ""
    all_candidates: List[Dict[str, Any]] = []

    expanded: List[str] = []
    seen_expanded: set[str] = set()
    for raw in queries:
        for query in expand_item_search_queries(raw):
            if query in seen_expanded:
                continue
            seen_expanded.add(query)
            expanded.append(query)

    expanded.sort(key=lambda value: (-_query_specificity(value), -len(value), value))

    for query in expanded:
        gid, name, mhn, score, candidates = lookup_item_in_catalog(query)
        all_candidates.extend(candidates)
        if score > best_score and gid is not None:
            best_score, best_gid, best_name, best_mhn, best_query = score, gid, name, mhn, query

        if best_score >= 0.85 and _query_specificity(best_query) >= 5:
            return best_gid, best_name, best_mhn, best_score, best_query, all_candidates[:8]

        gid, name, mhn, score, candidates = lookup_item_hybrid(query)
        all_candidates.extend(candidates)
        if score > best_score and gid is not None:
            best_score, best_gid, best_name, best_mhn, best_query = score, gid, name, mhn, query
            if best_score >= 0.5 and _query_specificity(best_query) >= 4:
                return best_gid, best_name, best_mhn, best_score, best_query, all_candidates[:8]

    return best_gid, best_name, best_mhn, best_score, best_query, all_candidates[:8]
