# -*- coding: utf-8 -*-
"""Lightweight market scans for CS chat (manipulation watchlist, heat movers)."""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

_MANIPULATION_INTENT_RE = re.compile(
    r"(做盘|控盘|对倒|诱多|庄家|操纵)",
    re.IGNORECASE,
)
_HEAT_INTENT_RE = re.compile(
    r"(热度.{0,6}上升|哪些.{0,8}活跃|最近哪些|涨得多|强势)",
    re.IGNORECASE,
)

_CATEGORY_SEEDS: Tuple[Tuple[str, int], ...] = (
    ("探员", 6),
    ("印花", 5),
    ("全息", 4),
    ("手套", 5),
    ("匕首", 5),
    ("纪念品", 4),
)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def detect_market_intent(message: str) -> str:
    text = (message or "").strip()
    if _MANIPULATION_INTENT_RE.search(text):
        return "manipulation"
    if _HEAT_INTENT_RE.search(text):
        return "heat"
    return "general"


def _suspicion_score(trend: Dict[str, Any], snapshot: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    bias = float(trend.get("bias_ma5") or 0)
    vr = float(trend.get("volume_ratio_5d") or 0)
    vol_status = str(trend.get("volume_status") or "")
    rsi_status = str(trend.get("rsi_status") or "")
    macd_status = str(trend.get("macd_status") or "")
    price = float(trend.get("current_price") or 0)

    yyyp_num = snapshot.get("yyyp_sell_num")
    buff_num = snapshot.get("buff_sell_num")
    listing = None
    for raw in (yyyp_num, buff_num):
        if raw is None:
            continue
        try:
            listing = int(raw)
            break
        except (TypeError, ValueError):
            continue

    if bias >= 8:
        score += 2.5
        reasons.append(f"乖离 MA5 达 {bias:.1f}%")
    elif bias >= 5:
        score += 1.5
        reasons.append(f"乖离 MA5 {bias:.1f}%")

    if vol_status == "缩量" and bias >= 4:
        score += 2.0
        reasons.append("价升量缩（筹码锁定嫌疑）")

    if vr >= 3 and bias < 2:
        score += 2.0
        reasons.append(f"量比 {vr:.1f} 但涨幅有限（对倒/做量嫌疑）")

    if "超买" in rsi_status or "偏高" in rsi_status:
        score += 1.0
        reasons.append(f"RSI 状态：{rsi_status}")

    if macd_status == "死叉" and bias >= 5:
        score += 1.5
        reasons.append("高位 MACD 死叉")

    if listing is not None and listing <= 25:
        score += 1.5
        reasons.append(f"挂牌量偏低（{listing}）")

    if price > 0 and listing is not None and listing <= 15 and vr >= 1.5:
        score += 1.0
        reasons.append("低挂牌+成交活跃")

    return round(score, 2), reasons


def _heat_score(trend: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []
    vr = float(trend.get("volume_ratio_5d") or 0)
    bias = float(trend.get("bias_ma5") or 0)
    signal = int(trend.get("signal_score") or 0)
    vol_status = str(trend.get("volume_status") or "")

    if vr >= 1.8:
        score += 2.0
        reasons.append(f"量比 {vr:.1f}")
    if bias >= 3:
        score += 1.5
        reasons.append(f"乖离 MA5 {bias:.1f}%")
    if vol_status == "放量":
        score += 1.5
        reasons.append("放量")
    if signal >= 60:
        score += 1.0
        reasons.append(f"信号分 {signal}")
    return round(score, 2), reasons


def _collect_candidate_good_ids(max_pool: int) -> List[Dict[str, Any]]:
    seen: set[int] = set()
    pool: List[Dict[str, Any]] = []

    try:
        from src.repositories.cs_item_catalog_repo import CSItemCatalogRepository

        repo = CSItemCatalogRepository()
        if repo.count_items() > 0:
            for term, limit in _CATEGORY_SEEDS:
                rows, _ = repo.search_items(term, page_size=limit)
                for row in rows:
                    gid = int(row.good_id)
                    if gid in seen:
                        continue
                    seen.add(gid)
                    pool.append(
                        {
                            "good_id": gid,
                            "name": row.name,
                            "market_hash_name": row.market_hash_name,
                            "seed": term,
                        }
                    )
                    if len(pool) >= max_pool:
                        return pool
    except Exception as exc:
        logger.debug("CS market scan catalog pool failed: %s", exc)

    try:
        from market_provider.csqaq.client import CSQAQClient

        client = CSQAQClient()
        for term, limit in _CATEGORY_SEEDS:
            result = client.search_goods(term, page_size=limit)
            for entry in result.items:
                gid = int(entry.id)
                if gid in seen:
                    continue
                seen.add(gid)
                pool.append(
                    {
                        "good_id": gid,
                        "name": entry.name,
                        "market_hash_name": entry.market_hash_name,
                        "seed": term,
                    }
                )
                if len(pool) >= max_pool:
                    return pool
    except Exception as exc:
        logger.debug("CS market scan CSQAQ search pool failed: %s", exc)

    return pool


def _verify_item_identity(good_id: int, fallback_name: str = "", fallback_mhn: str = "") -> Dict[str, str]:
    """Resolve canonical item name from CSQAQ / catalog — never trust LLM to rewrite."""
    try:
        from market_provider.csqaq.item_analysis import fetch_item_snapshot
        from market_provider.csqaq.client import CSQAQClient

        goods = fetch_item_snapshot(CSQAQClient(), int(good_id))
        name = str(goods.get("name") or fallback_name or good_id).strip()
        mhn = str(goods.get("market_hash_name") or fallback_mhn or name).strip()
        return {"name": name, "market_hash_name": mhn}
    except Exception as exc:
        logger.debug("verify item identity failed good_id=%s: %s", good_id, exc)

    try:
        from src.repositories.cs_item_catalog_repo import CSItemCatalogRepository

        catalog_row = CSItemCatalogRepository().get_by_good_id(int(good_id))
        if catalog_row is not None:
            return {
                "name": str(catalog_row.name),
                "market_hash_name": str(catalog_row.market_hash_name or catalog_row.name),
            }
    except Exception:
        pass

    return {
        "name": (fallback_name or str(good_id)).strip(),
        "market_hash_name": (fallback_mhn or fallback_name or str(good_id)).strip(),
    }


def render_watchlist_markdown(watchlist: List[Dict[str, Any]]) -> str:
    """Pre-render table for LLM to copy verbatim — reduces name hallucination."""
    if not watchlist:
        return (
            "_（本次扫描未产出达到阈值的单品；请勿捏造饰品名，仅可说明方法论或建议同步商品库后重试。）_"
        )
    lines = [
        "| good_id | 饰品全称（禁止改写） | 可疑/强势信号 | 现价 |",
        "| --- | --- | --- | --- |",
    ]
    for row in watchlist:
        gid = row.get("good_id")
        name = str(row.get("name") or "").replace("|", "/")
        reasons = "；".join(row.get("reasons") or []) or "-"
        price = row.get("current_price")
        price_text = f"{float(price):.2f}" if price is not None else "-"
        lines.append(f"| {gid} | {name} | {reasons} | {price_text} |")
    return "\n".join(lines)


def build_authorized_items(watchlist: List[Dict[str, Any]], category_examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flat allow-list of items the model may cite by name."""
    authorized: List[Dict[str, Any]] = []
    seen: set[int] = set()
    for row in watchlist:
        gid = row.get("good_id")
        if gid is None:
            continue
        try:
            gid_int = int(gid)
        except (TypeError, ValueError):
            continue
        if gid_int in seen:
            continue
        seen.add(gid_int)
        authorized.append(
            {
                "good_id": gid_int,
                "name": row.get("name"),
                "market_hash_name": row.get("market_hash_name"),
                "source": "watchlist",
            }
        )
    for block in category_examples:
        for ex in block.get("examples") or []:
            gid = ex.get("good_id")
            if gid is None:
                continue
            try:
                gid_int = int(gid)
            except (TypeError, ValueError):
                continue
            if gid_int in seen:
                continue
            seen.add(gid_int)
            authorized.append(
                {
                    "good_id": gid_int,
                    "name": ex.get("name"),
                    "source": "category_example",
                }
            )
    return authorized


def _analyze_candidate(good_id: int, *, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        from src.services.cs_item_service import CSItemService

        payload = CSItemService().analyze_item(
            good_id=good_id,
            platform=platform,
            period=90,
            prefer_crawl=True,
            refresh_crawl=False,
            refresh_today=False,
            kline_pages=1,
            include_report=False,
            skills=None,
        )
        return payload
    except Exception as exc:
        logger.debug("CS market scan analyze failed good_id=%s: %s", good_id, exc)
        return None


def scan_market_watchlist(
    message: str,
    *,
    platform: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a concrete item watchlist for market-scope chat.

    Not a full-market exhaustive scan — samples category seeds then ranks by heuristics.
    """
    intent = detect_market_intent(message)
    max_pool = _env_int("CS_CHAT_MARKET_SCAN_POOL", 24)
    max_analyze = _env_int("CS_CHAT_MARKET_SCAN_MAX_ITEMS", 6)
    min_score = float(os.getenv("CS_CHAT_MARKET_SCAN_MIN_SCORE", "2.5"))

    pool = _collect_candidate_good_ids(max_pool)
    result: Dict[str, Any] = {
        "intent": intent,
        "scan_method": "category_seed_sample",
        "pool_size": len(pool),
        "analyzed_count": 0,
        "watchlist": [],
        "category_examples": [],
    }

    if not pool:
        result["note"] = (
            "未能获取候选饰品池：请配置 CSQAQ_API_TOKEN 并执行 "
            "`python scripts/sync_cs_item_catalog.py --mode full` 同步商品库后重试。"
        )
        return result

    # Surface raw examples even before analyze (so LLM can name items if analyze fails).
    by_seed: Dict[str, List[Dict[str, Any]]] = {}
    for row in pool:
        by_seed.setdefault(str(row.get("seed") or "其他"), []).append(
            {
                "good_id": row["good_id"],
                "name": row["name"],
            }
        )
    result["category_examples"] = [
        {"category": seed, "examples": items[:4]}
        for seed, items in by_seed.items()
    ]

    ranked: List[Dict[str, Any]] = []
    for row in pool[:max_analyze]:
        payload = _analyze_candidate(int(row["good_id"]), platform=platform)
        result["analyzed_count"] += 1
        if not payload:
            continue
        trend = payload.get("trend") or {}
        snapshot = payload.get("snapshot") or {}
        if intent == "heat":
            score, reasons = _heat_score(trend)
        else:
            score, reasons = _suspicion_score(trend, snapshot)
        if score < min_score and intent == "manipulation":
            continue
        gid = int(payload.get("good_id") or row["good_id"])
        identity = _verify_item_identity(
            gid,
            fallback_name=str(payload.get("item_name") or row.get("name") or gid),
            fallback_mhn=str(payload.get("market_hash_name") or row.get("market_hash_name") or ""),
        )
        ranked.append(
            {
                "good_id": gid,
                "name": identity["name"],
                "market_hash_name": identity["market_hash_name"],
                "seed_category": row.get("seed"),
                "score": score,
                "reasons": reasons,
                "current_price": trend.get("current_price"),
                "bias_ma5": trend.get("bias_ma5"),
                "volume_ratio_5d": trend.get("volume_ratio_5d"),
                "volume_status": trend.get("volume_status"),
                "buy_signal": trend.get("buy_signal"),
                "signal_score": trend.get("signal_score"),
                "yyyp_sell_num": snapshot.get("yyyp_sell_num"),
                "buff_sell_num": snapshot.get("buff_sell_num"),
            }
        )

    ranked.sort(key=lambda item: float(item.get("score") or 0), reverse=True)
    result["watchlist"] = ranked[:8]
    result["authorized_items"] = build_authorized_items(result["watchlist"], result["category_examples"])
    result["watchlist_table_markdown"] = render_watchlist_markdown(result["watchlist"])

    if intent == "manipulation":
        result["note"] = (
            "watchlist 为品类种子抽样 + 技术可疑度排序，非全市场穷尽扫描；"
            "回答时必须优先列出 watchlist 中具体饰品名称与可疑信号，识别框架放后。"
        )
    elif intent == "heat":
        result["note"] = (
            "watchlist 为近期量能/乖离偏强的抽样候选；优先列出具体饰品名与数据，再补充品类趋势。"
        )
    else:
        result["note"] = "已提供品类示例与指数数据；若用户问「哪些」，尽量引用 category_examples 与 watchlist。"

    return result
