# -*- coding: utf-8 -*-
"""
CS chat pipeline: Entity → Memory → Data → Skills → LLM narrator payload.

Replaces scope-only routing with session-aware item binding and code-first analysis.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional

from src.services.cs_chat_session import (
    clear_pending_item_query,
    get_current_item,
    get_last_intent,
    get_pending_item_query,
    set_current_item,
    set_last_intent,
    set_pending_item_query,
)
from src.services.cs_entity_resolver import (
    INTENT_MARKET_SCAN,
    ResolvedEntity,
    _EXPLICIT_MARKET_SCAN_RE,
    _PORTFOLIO_RE,
    _extract_item_query_candidates,
    resolve_entities,
)
from src.services.cs_item_data_provider import ItemDataBundle, ItemDataProvider
from src.services.cs_skill_engine import CSSkillEngine, SkillEngineResult

logger = logging.getLogger(__name__)

ChatPipelineScope = Literal["market", "portfolio", "single_item", "general"]


@dataclass
class ChatPipelineResult:
    scope: ChatPipelineScope
    intent: str
    entity: ResolvedEntity
    item_bundle: Optional[ItemDataBundle] = None
    skill_result: Optional[SkillEngineResult] = None
    market_block: Optional[Dict[str, Any]] = None
    portfolio_block: Optional[Dict[str, Any]] = None
    previous_summary: str = ""
    session_item: Optional[Dict[str, Any]] = None
    narrator_payload: Dict[str, Any] = field(default_factory=dict)


def resolve_pipeline_scope(
    message: str,
    entity: ResolvedEntity,
    *,
    explicit_scope: Optional[str] = None,
    session_item: Optional[Dict[str, Any]] = None,
) -> ChatPipelineScope:
    allowed = ("market", "portfolio", "single_item", "general")
    if explicit_scope in allowed and explicit_scope != "general":
        return explicit_scope  # type: ignore[return-value]

    text = (message or "").strip()

    if _PORTFOLIO_RE.search(text):
        return "portfolio"

    if entity.intent == INTENT_MARKET_SCAN or _EXPLICIT_MARKET_SCAN_RE.search(text):
        return "market"

    if entity.good_id is not None:
        return "single_item"

    if session_item and session_item.get("good_id") is not None:
        if entity.intent != INTENT_MARKET_SCAN and not _EXPLICIT_MARKET_SCAN_RE.search(text):
            return "single_item"

    return "general"


def _fetch_market_block(message: str) -> Dict[str, Any]:
    from src.services.cs_chat_scope import _fetch_market_context

    return _fetch_market_context(message)


def _fetch_portfolio_block() -> Dict[str, Any]:
    from src.services.cs_chat_scope import _fetch_portfolio_context

    return _fetch_portfolio_context()


def run_cs_chat_pipeline(
    *,
    session_id: str,
    message: str,
    request_context: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> ChatPipelineResult:
    """
    Execute Entity → Memory → Data → Skills pipeline for one chat turn.
    """
    ctx = dict(request_context or {})
    explicit_scope = str(ctx.pop("scope", "") or "").strip() or None
    previous_summary = str(
        ctx.get("previous_analysis_summary") or ctx.get("previous_report") or ""
    ).strip()
    platform = ctx.get("platform")

    session_item = get_current_item(session_id)
    last_intent = get_last_intent(session_id)

    pending_query = get_pending_item_query(session_id)

    if progress_callback and _extract_item_query_candidates(message):
        progress_callback({"type": "generating", "message": "正在通过 CSQAQ 网站检索饰品…"})

    entity = resolve_entities(
        message,
        request_context=ctx,
        session_item=session_item,
        last_intent=last_intent,
        pending_item_query=pending_query,
    )
    set_last_intent(session_id, entity.intent)

    if entity.good_id is not None:
        clear_pending_item_query(session_id)
    elif entity.item_query and not _EXPLICIT_MARKET_SCAN_RE.search(message):
        set_pending_item_query(session_id, entity.item_query)

    scope = resolve_pipeline_scope(
        message,
        entity,
        explicit_scope=explicit_scope,
        session_item=session_item,
    )

    if scope == "market" and explicit_scope != "market":
        if entity.good_id and not _EXPLICIT_MARKET_SCAN_RE.search(message):
            if entity.intent != INTENT_MARKET_SCAN:
                scope = "single_item"

    result = ChatPipelineResult(
        scope=scope,
        intent=entity.intent,
        entity=entity,
        previous_summary=previous_summary,
        session_item=session_item,
    )

    provider = ItemDataProvider()
    engine = CSSkillEngine()

    if scope == "single_item" and entity.good_id is not None:
        set_current_item(
            session_id,
            good_id=int(entity.good_id),
            item_name=entity.item_name,
            market_hash_name=entity.market_hash_name,
            platform=str(platform) if platform else None,
        )
        bundle = provider.fetch_with_backfill(
            good_id=int(entity.good_id),
            item=entity.item_name or entity.item_query,
            platform=str(platform) if platform else None,
            progress_callback=progress_callback,
        )
        result.item_bundle = bundle
        result.skill_result = engine.run(entity.intent, bundle)
        result.session_item = get_current_item(session_id)
        result.narrator_payload = _build_single_item_payload(result)
        return result

    if scope == "market":
        result.market_block = _fetch_market_block(message)
        result.narrator_payload = {
            "mode": "market",
            "intent": entity.intent,
            "market": result.market_block,
        }
        return result

    if scope == "portfolio":
        result.portfolio_block = _fetch_portfolio_block()
        result.narrator_payload = {
            "mode": "portfolio",
            "intent": entity.intent,
            "portfolio": result.portfolio_block,
        }
        return result

    if entity.good_id is not None:
        set_current_item(
            session_id,
            good_id=int(entity.good_id),
            item_name=entity.item_name,
            market_hash_name=entity.market_hash_name,
        )
        bundle = provider.fetch_with_backfill(
            good_id=int(entity.good_id),
            item=entity.item_name or entity.item_query,
            platform=str(platform) if platform else None,
            progress_callback=progress_callback,
        )
        result.item_bundle = bundle
        result.skill_result = engine.run(entity.intent, bundle)
        result.scope = "single_item"
        result.narrator_payload = _build_single_item_payload(result)
        return result

    result.narrator_payload = {
        "mode": "general",
        "intent": entity.intent,
        "previous_summary": previous_summary[:2000] if previous_summary else "",
        "session_item": session_item,
        "entity": {
            "item_query": entity.item_query,
            "catalog_candidates": entity.catalog_candidates[:5],
            "resolution_failed": True,
        },
        "resolution_hint": (
            "未能解析 good_id：请检查 CSQAQ Token/IP 白名单，或确认 Playwright 可用。"
            "不要要求用户「发起首页分析」——系统已尝试本地库、Open API 与浏览器检索。"
        ),
    }
    return result


def _build_single_item_payload(pipeline: ChatPipelineResult) -> Dict[str, Any]:
    entity = pipeline.entity
    bundle = pipeline.item_bundle
    skills = pipeline.skill_result
    return {
        "mode": "single_item",
        "intent": pipeline.intent,
        "item": {
            "good_id": entity.good_id,
            "name": entity.item_name or (bundle.item_info.get("name") if bundle else ""),
            "resolution_source": entity.source,
            "confidence": entity.confidence,
        },
        "analysis": skills.to_dict() if skills else {},
        "data": bundle.to_dict() if bundle else {},
        "previous_summary": pipeline.previous_summary[:2000] if pipeline.previous_summary else "",
    }


def build_narrator_context_block(pipeline: ChatPipelineResult) -> str:
    """Render system-prompt appendix for LLM narrator."""
    parts: List[str] = [
        "## 本轮管线结果",
        f"- **scope**: `{pipeline.scope}`",
        f"- **intent**: `{pipeline.intent}`",
        f"- **entity_source**: `{pipeline.entity.source}`",
    ]

    if pipeline.session_item:
        parts.append(
            f"- **session_item**: good_id={pipeline.session_item.get('good_id')} "
            f"({pipeline.session_item.get('item_name') or ''})"
        )

    payload = pipeline.narrator_payload
    mode = payload.get("mode")

    if mode == "single_item":
        parts.append(
            "## 代码分析结论（LLM 只能解释，禁止重新分析或捏造）\n"
            "回答结构：**先结论，后依据**。\n\n"
            "```json\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n```"
        )
        manip = (payload.get("analysis") or {}).get("manipulation") or {}
        if manip:
            parts.append(
                "### 做盘结论速览\n"
                f"- 做盘评分：{manip.get('score')} / 100\n"
                f"- 概率：{manip.get('probability')}\n"
                f"- 信号：{'; '.join(manip.get('signals') or [])}"
            )
    elif mode == "market":
        market = payload.get("market") or {}
        table_md = market.get("watchlist_table_markdown") or ""
        if table_md:
            parts.append(
                "## 预生成候选表（必须原样放入回答，禁止改写饰品名）\n\n" + table_md
            )
        parts.append(
            "## 全市场扫描数据（JSON）\n```json\n"
            + json.dumps(market, ensure_ascii=False, indent=2)
            + "\n```"
        )
    elif mode == "portfolio":
        parts.append(
            "## 持仓快照（JSON）\n```json\n"
            + json.dumps(payload.get("portfolio") or {}, ensure_ascii=False, indent=2)
            + "\n```"
        )
    else:
        parts.append(
            "## 通用上下文（JSON）\n```json\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n```"
        )

    return "\n\n".join(parts).strip()


def try_build_resolution_failure_reply(pipeline: ChatPipelineResult) -> Optional[str]:
    """
    When item name was understood but good_id/data pipeline could not run,
    return a deterministic reply instead of letting the LLM ask the user to
    «go run home-page analysis».
    """
    entity = pipeline.entity
    item_query = str(entity.item_query or "").strip()
    if not item_query and entity.item_name:
        item_query = str(entity.item_name).strip()

    bundle = pipeline.item_bundle
    data_missing = (
        pipeline.scope == "single_item"
        and bundle is not None
        and (bundle.error or not bundle.trend)
        and not (bundle.price_history or [])
    )

    payload = pipeline.narrator_payload or {}
    entity_info = payload.get("entity") or {}
    resolution_failed = bool(entity_info.get("resolution_failed")) or (
        entity.good_id is None and bool(item_query)
    )

    if not resolution_failed and not data_missing:
        return None
    if not item_query and entity.good_id is None:
        return None

    import os

    token_ok = bool(os.getenv("CSQAQ_API_TOKEN", "").strip())
    catalog_hint = "本地商品库条目较少或未同步" if not entity_info.get("catalog_candidates") else "本地商品库未命中该名称"

    display_name = item_query or entity.item_name or str(entity.good_id or "该饰品")
    lines = [
        f"**暂时无法对「{display_name}」给出数据化结论。**",
        "",
        "系统已自动尝试：本地商品库检索 → CSQAQ Open API → 浏览器检索 →（若已有 good_id）K 线爬取，但当前未完成解析或拉数。",
        "",
        f"- **常见原因**：{catalog_hint}；CSQAQ Open API 返回 **401**（Token 无效或未加入 IP 白名单）。",
        f"- **ApiToken 已配置**：{'是' if token_ok else '否（请在 .env 设置 CSQAQ_API_TOKEN）'}",
        "",
        "**建议操作（按顺序）：**",
        "1. 运行 `python tools/probe_csqaq_api.py` 确认 search 接口返回 OK（401 需修正 Token / 公网 IP 白名单后重启后端）。",
        "2. 运行 `python scripts/sync_cs_item_catalog.py --mode full` 同步全量商品库（减少远程检索失败）。",
        "3. 同步成功后，在问饰品中重新发送饰品全名（如 `M4A1-S | 闪回` 或 `M4A1 闪回`）。",
        "",
        "修复上述配置后，问饰品会自动解析 good_id、爬取 K 线/成交量并给出 Skill 分析，无需手动去首页点分析。",
    ]
    if data_missing and entity.good_id is not None:
        lines.insert(
            1,
            f"（已解析 good_id={entity.good_id}，但 K 线/分析数据拉取失败：{bundle.error or '空数据'}）",
        )
    return "\n".join(lines)
