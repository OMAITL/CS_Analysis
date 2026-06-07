# -*- coding: utf-8 -*-
"""CS item tools — agent-callable wrappers for CS chat (ReAct mode)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.agent.tools.registry import ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)

_OHLCV_TAIL = 30


def _compact_ohlcv(rows: List[Dict[str, Any]], *, tail: int = _OHLCV_TAIL) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in list(rows or [])[-tail:]:
        out.append(
            {
                "date": row.get("date"),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "change_percent": row.get("change_percent") or row.get("pct_chg"),
            }
        )
    return out


def _handle_search_cs_item(query: str, page_size: int = 8) -> Dict[str, Any]:
    text = (query or "").strip()
    if not text:
        return {"status": "error", "error": "query is required", "items": []}

    try:
        from src.services.cs_item_resolve_service import resolve_good_id_from_queries

        gid, name, mhn, score, best_query, candidates = resolve_good_id_from_queries([text])
        items = [
            {
                "good_id": int(row.get("good_id")),
                "name": row.get("name"),
                "market_hash_name": row.get("market_hash_name"),
                "score": row.get("score"),
                "source": row.get("source"),
            }
            for row in (candidates or [])
            if row.get("good_id") is not None
        ]
        dedup: Dict[int, Dict[str, Any]] = {}
        for row in items:
            dedup[int(row["good_id"])] = row
        items = list(dedup.values())[: max(1, min(int(page_size or 8), 20))]

        return {
            "status": "ok",
            "query": text,
            "best_query": best_query,
            "best_match": {
                "good_id": gid,
                "name": name,
                "market_hash_name": mhn,
                "score": score,
            }
            if gid is not None
            else None,
            "items": items,
            "note": (
                "同名皮肤可能有多种磨损档；若用户未指定磨损，列出候选并请用户确认，"
                "或根据上下文选择最合理的一档后再调用 analyze_cs_item。"
            ),
        }
    except Exception as exc:
        logger.warning("search_cs_item failed for %r: %s", text, exc)
        return {"status": "error", "error": str(exc), "query": text, "items": []}


def _handle_analyze_cs_item(
    good_id: int,
    item: str = "",
    platform: str = "yyyp",
    period: int = 180,
    refresh_crawl: bool = False,
) -> Dict[str, Any]:
    try:
        gid = int(good_id)
    except (TypeError, ValueError):
        return {"status": "error", "error": "good_id must be an integer"}

    plat = (platform or "yyyp").strip().lower() or "yyyp"
    try:
        days = max(30, min(int(period or 180), 365))
    except (TypeError, ValueError):
        days = 180

    try:
        from src.services.cs_item_data_provider import ItemDataProvider

        bundle = ItemDataProvider().fetch_with_backfill(
            good_id=gid,
            item=(item or "").strip() or None,
            platform=plat,
            period=days,
            progress_callback=None,
        )
        if bundle.error and not bundle.trend and not bundle.price_history:
            return {
                "status": "error",
                "good_id": gid,
                "error": bundle.error,
                "item_info": bundle.item_info,
                "meta": bundle.meta,
            }

        trend = dict(bundle.trend or {})
        snapshot = dict(bundle.item_info or {})
        return {
            "status": "ok",
            "good_id": bundle.good_id or gid,
            "item_name": snapshot.get("name") or item,
            "market_hash_name": snapshot.get("market_hash_name"),
            "platform": plat,
            "trend": trend,
            "snapshot": {
                k: snapshot.get(k)
                for k in (
                    "buff_sell_price",
                    "yyyp_sell_price",
                    "steam_sell_price",
                    "buff_sell_num",
                    "yyyp_sell_num",
                    "turnover_number",
                    "data_sources",
                    "api_snapshot_error",
                )
                if snapshot.get(k) is not None
            },
            "recent_daily_bars": _compact_ohlcv(bundle.price_history or []),
            "meta": dict(bundle.meta or {}),
            "error": bundle.error,
            "note": (
                "K 线 volume 为日成交笔数；buff/yyyp sell_num 为挂牌量不是成交量。"
                "data_quality 非 full 时须在结论中说明不确定性。"
            ),
        }
    except Exception as exc:
        logger.warning("analyze_cs_item failed good_id=%s: %s", gid, exc)
        return {"status": "error", "good_id": gid, "error": str(exc)}


def _handle_search_cs_item_intel(good_id: int, max_items: int = 6) -> Dict[str, Any]:
    try:
        gid = int(good_id)
    except (TypeError, ValueError):
        return {"status": "error", "error": "good_id must be an integer"}

    try:
        from src.services.cs_event_intel_service import fetch_cs_event_intel

        payload = fetch_cs_event_intel(good_id=gid)
        items = list(payload.get("items") or payload.get("intel_items") or [])[: max(1, min(int(max_items or 6), 12))]
        return {
            "status": "ok",
            "good_id": gid,
            "item_name": payload.get("item_name") or payload.get("name"),
            "items": items,
            "summary": payload.get("summary") or payload.get("note"),
        }
    except Exception as exc:
        logger.warning("search_cs_item_intel failed good_id=%s: %s", gid, exc)
        return {"status": "error", "good_id": gid, "error": str(exc), "items": []}


def _handle_get_cs_market_overview(include_watchlist: bool = False) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"status": "ok"}
    try:
        from src.services.cs_skill_prompt import fetch_cs_index_summary

        summary = fetch_cs_index_summary()
        if summary:
            payload["index_summary"] = summary
    except Exception as exc:
        payload["index_summary_error"] = str(exc)

    try:
        from market_provider.csqaq.client import CSQAQClient

        indexes = CSQAQClient().list_sub_indexes()
        payload["sub_indexes"] = [
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "price": row.get("price") or row.get("sell_price") or row.get("close"),
                "change": row.get("change") or row.get("change_percent") or row.get("pct_chg"),
            }
            for row in (indexes or [])[:12]
            if isinstance(row, dict)
        ]
    except Exception as exc:
        payload["sub_indexes_error"] = str(exc)

    if include_watchlist:
        try:
            from src.services.cs_market_scan_service import scan_market_watchlist

            scan = scan_market_watchlist("")
            payload["watchlist"] = scan.get("watchlist") or []
            payload["authorized_items"] = scan.get("authorized_items") or []
            if scan.get("watchlist_table_markdown"):
                payload["watchlist_table_markdown"] = scan["watchlist_table_markdown"]
        except Exception as exc:
            payload["watchlist_error"] = str(exc)

    return payload


def _handle_get_cs_portfolio_snapshot() -> Dict[str, Any]:
    try:
        from src.services.cs_holdings_service import CSHoldingsService

        snapshot = CSHoldingsService().get_snapshot(refresh_prices=False)
        items = list(snapshot.get("items") or [])
        return {
            "status": "ok",
            "summary": snapshot.get("summary") or {},
            "items": items[:20],
            "truncated": len(items) > 20,
            "note": "价格为库内缓存；单品技术诊断需对具体 good_id 调用 analyze_cs_item。",
        }
    except Exception as exc:
        logger.warning("get_cs_portfolio_snapshot failed: %s", exc)
        return {"status": "error", "error": str(exc), "items": []}


search_cs_item_tool = ToolDefinition(
    name="search_cs_item",
    description=(
        "Search CS2 skin/item by Chinese or English name and resolve CSQAQ good_id. "
        "Use when the user mentions an item name but good_id is unknown. "
        "Returns multiple wear variants when ambiguous."
    ),
    parameters=[
        ToolParameter(name="query", type="string", description="Item name fragment, e.g. 'M4A1 闪回' or '蝴蝶刀 多普勒'"),
        ToolParameter(
            name="page_size",
            type="integer",
            description="Max candidates to return (default 8).",
            required=False,
            default=8,
        ),
    ],
    handler=_handle_search_cs_item,
    category="data",
)

analyze_cs_item_tool = ToolDefinition(
    name="analyze_cs_item",
    description=(
        "Fetch OHLCV, platform prices, and technical trend indicators for one CS item good_id. "
        "Always call this before giving buy/sell/hold advice on a specific item."
    ),
    parameters=[
        ToolParameter(name="good_id", type="integer", description="CSQAQ good_id"),
        ToolParameter(name="item", type="string", description="Optional display name hint.", required=False, default=""),
        ToolParameter(
            name="platform",
            type="string",
            description="Price platform: yyyp, buff, or steam (default yyyp).",
            required=False,
            default="yyyp",
        ),
        ToolParameter(name="period", type="integer", description="History days (30-365, default 180).", required=False, default=180),
        ToolParameter(
            name="refresh_crawl",
            type="boolean",
            description="Force Playwright K-line crawl when local/API data missing.",
            required=False,
            default=False,
        ),
    ],
    handler=_handle_analyze_cs_item,
    category="analysis",
)

search_cs_item_intel_tool = ToolDefinition(
    name="search_cs_item_intel",
    description="Search recent CS2 news/event intel related to a specific item good_id.",
    parameters=[
        ToolParameter(name="good_id", type="integer", description="CSQAQ good_id"),
        ToolParameter(name="max_items", type="integer", description="Max intel rows (default 6).", required=False, default=6),
    ],
    handler=_handle_search_cs_item_intel,
    category="search",
)

get_cs_market_overview_tool = ToolDefinition(
    name="get_cs_market_overview",
    description="Get CS market index summary and optional watchlist scan for broad market questions.",
    parameters=[
        ToolParameter(
            name="include_watchlist",
            type="boolean",
            description="When true, include sampled watchlist candidates for manipulation/trend scan.",
            required=False,
            default=False,
        ),
    ],
    handler=_handle_get_cs_market_overview,
    category="data",
)

get_cs_portfolio_snapshot_tool = ToolDefinition(
    name="get_cs_portfolio_snapshot",
    description="Get user's CS holdings snapshot for portfolio-level questions.",
    parameters=[],
    handler=_handle_get_cs_portfolio_snapshot,
    category="data",
)

ALL_CS_TOOLS = [
    search_cs_item_tool,
    analyze_cs_item_tool,
    search_cs_item_intel_tool,
    get_cs_market_overview_tool,
    get_cs_portfolio_snapshot_tool,
]
