# -*- coding: utf-8 -*-
"""Entity resolver: extract CS item names and user intent from chat messages."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

INTENT_MANIPULATION = "manipulation"
INTENT_MARKET_SCAN = "market_scan"
INTENT_BUY_SELL = "buy_sell"
INTENT_RISK = "risk"
INTENT_TREND = "trend"
INTENT_EXPLAIN = "explain"
INTENT_GENERAL = "general"

_PORTFOLIO_RE = re.compile(
    r"(我持有|我的持仓|持仓里|持仓中|我的库存|我手里|我买的|持仓的|库存里|我仓位)",
    re.IGNORECASE,
)
_EXPLICIT_MARKET_SCAN_RE = re.compile(
    r"(哪些饰品|哪些刀|哪些枪|哪些手套|哪些皮肤|哪些品类|哪类饰品|哪种刀|"
    r"全市场|整个市场|还有别的|其他可能|还有哪些|最近哪些.{0,8}活跃)",
    re.IGNORECASE,
)
_MANIPULATION_RE = re.compile(r"(做盘|控盘|对倒|诱多|庄家|操纵)", re.IGNORECASE)
_BUY_SELL_RE = re.compile(
    r"(要不要买|要不要卖|要不要出货|是否减仓|适合入手|适合观望|还能不能拿|要不要跑|"
    r"卖掉|买入|抄底|追高)",
    re.IGNORECASE,
)
_RISK_RE = re.compile(r"(风险|高位|止损|回撤|泡沫)", re.IGNORECASE)
_TREND_RE = re.compile(r"(趋势|走势|方向|看涨|看跌|突破|支撑|压力)", re.IGNORECASE)
_EXPLAIN_RE = re.compile(
    r"(你怎么知道|为什么|依据什么|怎么判断|怎么识别|是不是有人|从哪.{0,4}推|"
    r"那怎么|如何得出|什么原理)",
    re.IGNORECASE,
)
_ITEM_PIPE_RE = re.compile(
    r"([\u4e00-\u9fffA-Za-z0-9\-\(\)★]+)\s*[|｜/]\s*([\u4e00-\u9fffA-Za-z0-9\-\(\)\s★]+)",
)
_WEAR_SUFFIX_RE = re.compile(
    r"\s*[\(（]?(崭新出厂|略有磨损|久经沙场|破损不堪|战痕累累|Factory New|Minimal Wear|"
    r"Field-Tested|Well-Worn|Battle-Scarred)[\)）]?\s*$",
    re.IGNORECASE,
)
_INTENT_NOISE_RE = re.compile(
    r"(是不是|是否|有没有|有人|吗|呢|啊|呀|请问|帮我|分析|看看|一下|怎么|如何|为什么|"
    r"你知道|从.*推|根据|因此|所以|那|饰品|皮肤|物品)",
    re.IGNORECASE,
)
_LEADING_NOISE_PREFIX_RE = re.compile(
    r"^(这个|那个|这款|那款|请问|帮我|麻烦|分析|看看|聊一下|说一下)\s*",
    re.IGNORECASE,
)
_FOLLOW_UP_ONLY_RE = re.compile(
    r"^(那|这|它|此|该|继续|接着|还有|然后|所以|因此|另外|再|也)[\s，,]?",
    re.IGNORECASE,
)
_KNIFE_NAMES = (
    "蝴蝶刀",
    "爪子刀",
    "熊刀",
    "折叠刀",
    "猎杀者匕首",
    "猎杀者",
    "弯刀",
    "短剑",
    "锯齿爪刀",
    "锯齿爪",
    "流浪者匕首",
    "流浪者",
    "骷髅匕首",
    "骷髅",
    "系绳匕首",
    "系绳",
    "求生匕首",
    "求生",
    "暗影双匕",
    "刺刀",
    "鲍伊猎刀",
    "鲍伊",
    "穿肠刀",
    "弯刀",
)
_KNIFE_PATTERN = "|".join(re.escape(k) for k in sorted(_KNIFE_NAMES, key=len, reverse=True))
_KNIFE_SKIN_RE = re.compile(
    rf"({_KNIFE_PATTERN})\s*([\u4e00-\u9fffA-Za-z0-9\-]+)",
    re.IGNORECASE,
)
_WEAPON_SKIN_IN_TEXT_RE = re.compile(
    r"([A-Za-z0-9]{2,}(?:-[A-Za-z0-9]+)?)\s*([\u4e00-\u9fff]{2,8})",
)


@dataclass
class ResolvedEntity:
    """Result of entity + intent resolution for one user turn."""

    item_query: str = ""
    item_name: str = ""
    good_id: Optional[int] = None
    market_hash_name: str = ""
    intent: str = INTENT_GENERAL
    confidence: float = 0.0
    source: str = "none"
    catalog_candidates: List[Dict[str, Any]] = field(default_factory=list)


def detect_intent(message: str, *, last_intent: Optional[str] = None) -> str:
    text = (message or "").strip()
    if _EXPLICIT_MARKET_SCAN_RE.search(text):
        return INTENT_MARKET_SCAN
    if _EXPLAIN_RE.search(text):
        if _MANIPULATION_RE.search(text) or last_intent == INTENT_MANIPULATION:
            return INTENT_MANIPULATION
        return INTENT_EXPLAIN
    if _MANIPULATION_RE.search(text):
        return INTENT_MANIPULATION
    if _BUY_SELL_RE.search(text):
        return INTENT_BUY_SELL
    if _RISK_RE.search(text):
        return INTENT_RISK
    if _TREND_RE.search(text):
        return INTENT_TREND
    if last_intent:
        return last_intent
    return INTENT_GENERAL


_LEADING_ITEM_RE = re.compile(
    r"^([\u4e00-\u9fffA-Za-z0-9\-]+(?:\s*[|｜/]\s*[\u4e00-\u9fffA-Za-z0-9\-\s]+)?)",
)


def _normalize_search_query(text: str) -> str:
    cleaned = text
    for pattern in (_MANIPULATION_RE, _EXPLAIN_RE, _BUY_SELL_RE, _RISK_RE, _TREND_RE, _INTENT_NOISE_RE):
        cleaned = pattern.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ，,。.?？!！")
    return cleaned


_TRAILING_PARTICLE_RE = re.compile(r"[呢吗啊呀]$")


_TRAILING_QUESTION_TAIL_RE = re.compile(
    r"(现在|最近|今天|当前|这款|那个|是不是|是否|有没有|适合|要不要|还能|可以|怎么|如何|"
    r"为什么|值得|入手|观望|出货|做盘|分析|看看|有人|知道|觉得|认为|请问|帮我).*$",
    re.IGNORECASE,
)


def _first_skin_token(text: str) -> str:
    cleaned = _TRAILING_QUESTION_TAIL_RE.sub("", _normalize_search_query(text)).strip()
    cleaned = re.split(r"\s+", cleaned, maxsplit=1)[0]
    return cleaned.strip(" ，,。.?？!！")


def _message_mentions_item_name(message: str) -> bool:
    """True when the user message likely names a specific item (not a pure follow-up)."""
    text = (message or "").strip()
    if not text:
        return False
    if _ITEM_PIPE_RE.search(text):
        return True
    if _KNIFE_SKIN_RE.search(text):
        return True
    if _WEAPON_SKIN_IN_TEXT_RE.search(text):
        return True
    for candidate in _extract_item_query_candidates(text, include_normalized_full=False):
        compact = re.sub(r"\s+", "", candidate)
        if len(compact) >= 4:
            return True
        if "|" in candidate or "｜" in candidate:
            return True
    return False


def _extract_item_query_candidates(
    message: str,
    *,
    include_normalized_full: bool = True,
) -> List[str]:
    text = _LEADING_NOISE_PREFIX_RE.sub("", (message or "").strip())
    if not text:
        return []

    candidates: List[str] = []
    seen: set[str] = set()

    def _add(raw: str) -> None:
        cleaned = _WEAR_SUFFIX_RE.sub("", (raw or "").strip())
        cleaned = _TRAILING_PARTICLE_RE.sub("", cleaned)
        cleaned = _normalize_search_query(cleaned)
        cleaned = _TRAILING_QUESTION_TAIL_RE.sub("", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ，,。.?？!！")
        if len(cleaned) < 2 or cleaned in seen:
            return
        seen.add(cleaned)
        candidates.append(cleaned)

    for match in _ITEM_PIPE_RE.finditer(text):
        weapon = match.group(1).strip()
        skin = match.group(2).strip()
        _add(f"{weapon} | {skin}")
        _add(f"{weapon} {skin}")
        _add(f"{weapon}{skin}")

    for match in _KNIFE_SKIN_RE.finditer(text):
        knife = match.group(1).strip()
        skin = _first_skin_token(match.group(2).strip())
        if len(skin) >= 2:
            _add(f"{knife} {skin}")
            _add(f"{knife}{skin}")

    for match in _WEAPON_SKIN_IN_TEXT_RE.finditer(text):
        weapon = match.group(1).strip()
        skin = _first_skin_token(match.group(2).strip())
        if len(skin) >= 2:
            _add(f"{weapon} {skin}")
            _add(f"{weapon} | {skin}")
            _add(f"{weapon}{skin}")

    lead = _LEADING_ITEM_RE.match(text)
    if lead:
        fragment = lead.group(1).strip()
        rest = text[len(fragment) :].strip()
        has_pipe = "|" in fragment or "｜" in fragment or "/" in fragment
        if has_pipe:
            _add(fragment)
        elif rest:
            first_token = _first_skin_token(rest)
            if len(first_token) >= 2:
                _add(f"{fragment} {first_token}")
                _add(f"{fragment} | {first_token}")
                _add(f"{fragment}{first_token}")
            else:
                _add(fragment)
        else:
            _add(fragment)

    if include_normalized_full:
        normalized_full = _normalize_search_query(text)
        if normalized_full:
            _add(normalized_full)

    for chunk in re.split(r"[，,。.?？!！\n]", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        if _ITEM_PIPE_RE.search(chunk) or _KNIFE_SKIN_RE.search(chunk):
            continue
        _add(chunk)

    candidates.sort(key=lambda value: (-len(re.sub(r"\s+", "", value)), -len(value), value))
    return candidates


def _score_catalog_match(query: str, row_name: str, row_mhn: str) -> float:
    from src.services.cs_item_resolve_service import score_item_match

    return score_item_match(query, row_name, row_mhn)


def _lookup_catalog(query: str) -> tuple[Optional[int], str, str, float, List[Dict[str, Any]]]:
    from src.services.cs_item_resolve_service import lookup_item_in_catalog

    return lookup_item_in_catalog(query)


def resolve_entities(
    message: str,
    *,
    request_context: Optional[Dict[str, Any]] = None,
    session_item: Optional[Dict[str, Any]] = None,
    last_intent: Optional[str] = None,
    pending_item_query: str = "",
) -> ResolvedEntity:
    """
    Resolve item entity and intent from user message.

    Priority for good_id: explicit request context → catalog match from message → session item.
    """
    text = (message or "").strip()
    ctx = request_context or {}
    intent = detect_intent(text, last_intent=last_intent)

    result = ResolvedEntity(intent=intent)

    ctx_good_id = ctx.get("good_id")
    ctx_name = str(ctx.get("item_name") or ctx.get("item") or "").strip()
    mentions_new_item = _message_mentions_item_name(text)
    is_pure_follow_up = bool(
        session_item
        and not mentions_new_item
        and (
            _FOLLOW_UP_ONLY_RE.search(text)
            or intent in {INTENT_EXPLAIN, INTENT_MANIPULATION, INTENT_RISK, INTENT_TREND, INTENT_BUY_SELL}
            and not _extract_item_query_candidates(text, include_normalized_full=False)
        )
    )

    if ctx_good_id is not None and not mentions_new_item:
        try:
            gid = int(ctx_good_id)
            result.good_id = gid
            result.item_name = ctx_name
            result.item_query = ctx_name or str(gid)
            result.confidence = 1.0
            result.source = "request_context"
            return result
        except (TypeError, ValueError):
            pass

    best_gid: Optional[int] = None
    best_name = ""
    best_mhn = ""
    best_score = 0.0
    best_query = ""
    all_candidates: List[Dict[str, Any]] = []

    query_candidates = _extract_item_query_candidates(text)
    if pending_item_query:
        query_candidates = [f"{pending_item_query} {q}".strip() for q in query_candidates] + query_candidates
        query_candidates.append(pending_item_query)

    from src.services.cs_item_resolve_service import resolve_good_id_from_queries

    best_gid, best_name, best_mhn, best_score, best_query, all_candidates = resolve_good_id_from_queries(
        query_candidates
    )

    if best_gid is not None:
        result.good_id = best_gid
        result.item_name = best_name
        result.market_hash_name = best_mhn
        result.item_query = best_query
        result.confidence = best_score
        result.source = "catalog" if best_score >= 0.85 else ("browser" if best_score >= 0.4 and any(
            c.get("source") == "browser" for c in all_candidates
        ) else "hybrid")
        result.catalog_candidates = all_candidates[:8]
        return result

    if query_candidates:
        result.item_query = query_candidates[0]
        result.catalog_candidates = all_candidates[:8]

    if (
        session_item
        and session_item.get("good_id") is not None
        and not mentions_new_item
        and (is_pure_follow_up or not query_candidates)
    ):
        result.good_id = int(session_item["good_id"])
        result.item_name = str(session_item.get("item_name") or "")
        result.market_hash_name = str(session_item.get("market_hash_name") or "")
        result.item_query = result.item_name or str(result.good_id)
        result.confidence = 0.9
        result.source = "session_memory"
        result.catalog_candidates = all_candidates[:5]
        return result

    result.catalog_candidates = all_candidates[:5]
    return result
