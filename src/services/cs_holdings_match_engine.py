# -*- coding: utf-8 -*-
"""Three-tier match engine for CS holdings import drafts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from src.services.cs_item_resolve_service import (
    expand_item_search_queries,
    lookup_item_hybrid,
    lookup_item_in_catalog,
    resolve_good_id_from_queries,
    score_item_match,
    strip_wear_suffix,
)

MatchTier = Literal["exact", "fuzzy", "remote", "none"]
MatchConfidence = Literal["high", "medium", "low"]


@dataclass
class MatchResult:
    good_id: Optional[int] = None
    item_name: str = ""
    market_hash_name: str = ""
    match_tier: MatchTier = "none"
    match_confidence: MatchConfidence = "low"
    match_score: float = 0.0
    candidates: List[Dict[str, Any]] = field(default_factory=list)


def _confidence_from_score(score: float, tier: MatchTier) -> MatchConfidence:
    if tier == "exact" or score >= 0.9:
        return "high"
    if score >= 0.5 or tier == "fuzzy":
        return "medium"
    return "low"


def _build_query(item_name: str, wear: str = "") -> str:
    name = strip_wear_suffix((item_name or "").strip())
    wear_text = (wear or "").strip()
    if wear_text and wear_text not in name and wear_text not in item_name:
        return f"{name} ({wear_text})"
    return name or (item_name or "").strip()


def match_holding_item(
    *,
    item_name: str,
    wear: str = "",
    good_id: Optional[int] = None,
) -> MatchResult:
    if good_id is not None:
        return MatchResult(
            good_id=int(good_id),
            item_name=item_name,
            match_tier="exact",
            match_confidence="high",
            match_score=1.0,
        )

    query = _build_query(item_name, wear)
    if not query:
        return MatchResult(item_name=item_name)

    # L1: exact / high-score local catalog
    gid, name, mhn, score, candidates = lookup_item_in_catalog(query)
    if gid is not None and score >= 0.95:
        tier: MatchTier = "exact"
        return MatchResult(
            good_id=gid,
            item_name=name or item_name,
            market_hash_name=mhn,
            match_tier=tier,
            match_confidence=_confidence_from_score(score, tier),
            match_score=score,
            candidates=candidates,
        )

    # L2: fuzzy local catalog
    if gid is not None and score >= 0.35:
        tier = "fuzzy"
        return MatchResult(
            good_id=gid,
            item_name=name or item_name,
            market_hash_name=mhn,
            match_tier=tier,
            match_confidence=_confidence_from_score(score, tier),
            match_score=score,
            candidates=candidates,
        )

    # L2b: multi-variant local resolve
    variants = expand_item_search_queries(query)
    best_score = 0.0
    best_row: Optional[Dict[str, Any]] = None
    all_candidates: List[Dict[str, Any]] = list(candidates)
    for variant in variants[:12]:
        gid2, name2, mhn2, score2, cands2 = lookup_item_in_catalog(variant)
        all_candidates.extend(cands2)
        if score2 > best_score and gid2 is not None:
            best_score = score2
            best_row = {
                "good_id": gid2,
                "name": name2,
                "market_hash_name": mhn2,
                "score": score2,
            }
    if best_row and best_score >= 0.35:
        tier = "fuzzy"
        return MatchResult(
            good_id=int(best_row["good_id"]),
            item_name=str(best_row.get("name") or item_name),
            market_hash_name=str(best_row.get("market_hash_name") or ""),
            match_tier=tier,
            match_confidence=_confidence_from_score(best_score, tier),
            match_score=best_score,
            candidates=all_candidates[:8],
        )

    # L3: remote hybrid (CSQAQ + catalog upsert)
    gid3, name3, mhn3, score3, candidates3 = lookup_item_hybrid(query)
    all_candidates.extend(candidates3)
    if gid3 is not None and score3 >= 0.25:
        tier = "remote"
        return MatchResult(
            good_id=gid3,
            item_name=name3 or item_name,
            market_hash_name=mhn3,
            match_tier=tier,
            match_confidence=_confidence_from_score(score3, tier),
            match_score=score3,
            candidates=all_candidates[:8],
        )

    # L3b: broader query expansion fallback
    gid4, name4, mhn4, score4, _, candidates4 = resolve_good_id_from_queries(variants)
    all_candidates.extend(candidates4)
    if gid4 is not None:
        tier = "remote"
        return MatchResult(
            good_id=gid4,
            item_name=name4 or item_name,
            market_hash_name=mhn4,
            match_tier=tier,
            match_confidence=_confidence_from_score(score4, tier),
            match_score=score4,
            candidates=all_candidates[:8],
        )

    return MatchResult(
        item_name=item_name,
        match_tier="none",
        match_confidence="low",
        match_score=max(score, best_score, score3, 0.0),
        candidates=all_candidates[:8],
    )


def rematch_with_manual_good_id(
    *,
    item_name: str,
    wear: str,
    good_id: int,
    candidate_name: str = "",
    candidate_mhn: str = "",
) -> MatchResult:
    name = candidate_name or item_name
    mhn = candidate_mhn or candidate_name or item_name
    score = score_item_match(_build_query(item_name, wear), name, mhn)
    return MatchResult(
        good_id=int(good_id),
        item_name=name,
        market_hash_name=mhn,
        match_tier="exact",
        match_confidence="high" if score >= 0.5 else "medium",
        match_score=max(score, 0.75),
        candidates=[
            {
                "good_id": int(good_id),
                "name": name,
                "market_hash_name": mhn,
                "score": round(max(score, 0.75), 3),
                "source": "manual",
            }
        ],
    )
