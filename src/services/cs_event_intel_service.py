# -*- coding: utf-8 -*-
"""CS item event intel — search at analyze time, persist snapshot, feed reports."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.config import get_config, resolve_news_window_days
from src.search_service import SearchResponse, SearchResult, get_search_service
from src.services.cs_item_intel_keywords import (
    CSItemIntelKeywords,
    RelevanceTier,
    build_cs_item_intel_keywords,
    resolve_item_containers,
    score_event_relevance,
)

logger = logging.getLogger(__name__)

_EVENT_DIMENSION_ORDER: Tuple[str, ...] = (
    "item_focus",
    "case_focus",
    "official_crawl",
    "hltv_crawl",
    "official_update",
    "new_case",
    "cs_market",
    "hltv",
    "major_sticker",
    "tieba",
)

_EVENT_DIMENSION_CAPS: Dict[str, int] = {
    "item_focus": 4,
    "case_focus": 3,
    "official_crawl": 2,
    "hltv_crawl": 2,
    "official_update": 1,
    "new_case": 1,
    "cs_market": 2,
    "hltv": 1,
    "major_sticker": 2,
    "tieba": 2,
}

_TIER_ORDER: Dict[RelevanceTier, int] = {"direct": 0, "case": 1, "market": 2, "drop": 99}
_TIER_LIMITS: Dict[RelevanceTier, int] = {"direct": 6, "case": 5, "market": 5, "drop": 0}


def _items_from_response(
    dimension: str,
    response: SearchResponse,
    *,
    max_items: int,
    keywords: CSItemIntelKeywords,
) -> List[Dict[str, Any]]:
    if not response or not response.success:
        return []
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for result in response.results:
        title = (result.title or "").strip()
        url = (result.url or "").strip()
        if not title and not url:
            continue
        tier = score_event_relevance(
            title=title,
            snippet=result.snippet or "",
            dimension=dimension,
            keywords=keywords,
        )
        if tier == "drop":
            continue
        scored.append(
            (
                _TIER_ORDER[tier],
                {
                    "title": title or url,
                    "snippet": (result.snippet or "")[:500],
                    "url": url,
                    "dimension": dimension,
                    "source": (result.source or "").strip(),
                    "published_date": result.published_date,
                    "relevance": tier,
                },
            )
        )
    scored.sort(key=lambda pair: pair[0])
    return [row for _, row in scored[:max_items]]


def _balanced_event_items(
    intel_results: Dict[str, SearchResponse],
    keywords: CSItemIntelKeywords,
) -> List[Dict[str, Any]]:
    tier_counts: Dict[RelevanceTier, int] = {"direct": 0, "case": 0, "market": 0, "drop": 0}
    merged: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for dimension in _EVENT_DIMENSION_ORDER:
        response = intel_results.get(dimension)
        if not response:
            continue
        cap = _EVENT_DIMENSION_CAPS.get(dimension, 2)
        for row in _items_from_response(
            dimension,
            response,
            max_items=cap,
            keywords=keywords,
        ):
            tier = row.get("relevance") or "market"
            if tier not in ("direct", "case", "market"):
                continue
            if tier_counts[tier] >= _TIER_LIMITS[tier]:
                continue
            url = row.get("url") or ""
            if url and url in seen_urls:
                continue
            merged.append(row)
            tier_counts[tier] += 1
            if url:
                seen_urls.add(url)

    merged.sort(key=lambda row: _TIER_ORDER.get(row.get("relevance"), 99))
    return merged


def _dicts_to_search_response(items: List[Dict[str, Any]], *, query: str, provider: str) -> SearchResponse:
    results = [
        SearchResult(
            title=str(item.get("title") or ""),
            snippet=str(item.get("snippet") or ""),
            url=str(item.get("url") or ""),
            source=str(item.get("source") or ""),
            published_date=item.get("published_date"),
        )
        for item in items
        if item.get("title") or item.get("url")
    ]
    return SearchResponse(
        query=query,
        results=results,
        provider=provider,
        success=bool(results),
    )


def _filter_crawl_dicts(
    items: List[Dict[str, Any]],
    *,
    dimension: str,
    keywords: CSItemIntelKeywords,
) -> List[Dict[str, Any]]:
    kept: List[Dict[str, Any]] = []
    for item in items:
        tier = score_event_relevance(
            title=str(item.get("title") or ""),
            snippet=str(item.get("snippet") or ""),
            dimension=dimension,
            keywords=keywords,
        )
        if tier == "drop":
            continue
        enriched = dict(item)
        enriched["relevance"] = tier
        kept.append(enriched)
    return kept


def _fetch_hltv_crawl_items(
    max_age_days: int,
    max_items: int,
    keywords: CSItemIntelKeywords,
) -> List[Dict[str, Any]]:
    cfg = get_config()
    if not getattr(cfg, "hltv_crawl_enabled", False):
        return []
    try:
        from crawlers.hltv import fetch_hltv_news

        cap = min(int(max_items), _EVENT_DIMENSION_CAPS["hltv_crawl"] * 3)
        rows = fetch_hltv_news(max_items=max(1, cap), max_age_days=max_age_days, fail_soft=True)
        items = [row.to_event_dict() for row in rows]
        return _filter_crawl_dicts(items, dimension="hltv_crawl", keywords=keywords)
    except Exception as exc:
        logger.warning("HLTV 爬虫跳过: %s", exc)
        return []


def _fetch_official_crawl_items(max_age_days: int, max_items: int) -> List[Dict[str, Any]]:
    cfg = get_config()
    if not getattr(cfg, "cs_official_feed_enabled", True):
        return []
    try:
        from crawlers.cs_official import fetch_cs_official_blog

        cap = min(int(max_items), _EVENT_DIMENSION_CAPS["official_crawl"])
        rows = fetch_cs_official_blog(max_items=max(1, cap), max_age_days=max_age_days, fail_soft=True)
        return [
            {**row.to_event_dict(), "relevance": "market"}
            for row in rows
        ]
    except Exception as exc:
        logger.warning("官方博客 RSS 跳过: %s", exc)
        return []


def fetch_cs_event_intel(
    good_id: int,
    item_name: str,
    market_hash_name: str,
    *,
    max_searches: Optional[int] = None,
    save_to_db: bool = True,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Run CS event searches (same lifecycle as stock news: on-demand per analyze).

    Returns:
        (formatted_report_text, flat_item_list)
    """
    cfg = get_config()
    if not getattr(cfg, "cs_event_intel_enabled", True):
        return "", []

    keywords = build_cs_item_intel_keywords(
        item_name=item_name,
        market_hash_name=market_hash_name,
        good_id=good_id,
        container_names=resolve_item_containers(good_id),
    )
    if keywords.case_labels:
        logger.info(
            "CS 事件情报: good_id=%s 所属武器箱=%s",
            good_id,
            ", ".join(keywords.case_labels),
        )

    limit = max_searches if max_searches is not None else getattr(
        cfg, "cs_event_intel_max_searches", 8
    )
    profile = getattr(cfg, "cs_news_strategy_profile", "medium")
    search_days = resolve_news_window_days(cfg.news_max_age_days, profile)

    intel_results: Dict[str, SearchResponse] = {}
    service = get_search_service()
    if service.is_available:
        intel_results = service.search_cs_event_intel(
            good_id=good_id,
            item_name=item_name,
            market_hash_name=market_hash_name,
            max_searches=max(1, int(limit)),
            search_days=search_days,
            case_labels=list(keywords.case_labels),
        )
    else:
        logger.info("CS 事件情报: 搜索服务不可用，使用爬虫/RSS 源")

    official_items = _fetch_official_crawl_items(
        search_days,
        getattr(cfg, "cs_official_feed_max_items", 5),
    )
    if official_items:
        intel_results["official_crawl"] = _dicts_to_search_response(
            official_items,
            query="cs:official-blog-rss",
            provider="CS-Official-RSS",
        )

    hltv_crawl_items = _fetch_hltv_crawl_items(
        search_days,
        getattr(cfg, "hltv_crawl_max_items", 4),
        keywords,
    )
    if hltv_crawl_items:
        intel_results["hltv_crawl"] = _dicts_to_search_response(
            hltv_crawl_items,
            query="hltv:news-sitemap",
            provider="HLTV-Crawl",
        )

    if not intel_results:
        return "", []

    report_text = get_search_service().format_cs_event_report(intel_results, item_name)
    items = _balanced_event_items(intel_results, keywords)

    if save_to_db and items:
        try:
            from src.storage import DatabaseManager

            query_id = str(uuid.uuid4())
            db = DatabaseManager()
            query_context = {
                "query_id": query_id,
                "query_source": "cs_analyze",
                "requester_platform": "api",
            }
            code = f"cs:{good_id}"
            for dim_name, response in intel_results.items():
                if response and response.success and response.results:
                    db.save_news_intel(
                        code=code,
                        name=item_name,
                        dimension=dim_name,
                        query=response.query,
                        response=response,
                        query_context=query_context,
                    )
        except Exception as exc:
            logger.warning("CS 事件情报落库失败: %s", exc)

    logger.info(
        "CS 事件情报完成: good_id=%s, 维度=%s, 展示条数=%s, direct=%s case=%s market=%s",
        good_id,
        len(intel_results),
        len(items),
        sum(1 for i in items if i.get("relevance") == "direct"),
        sum(1 for i in items if i.get("relevance") == "case"),
        sum(1 for i in items if i.get("relevance") == "market"),
    )
    return report_text, items
