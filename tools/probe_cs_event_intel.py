#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe CS event intel search results and relevance scoring for one item."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import get_config, resolve_news_window_days, setup_env

setup_env()

from market_provider.csqaq.client import CSQAQClient  # noqa: E402
from src.search_service import SearchResponse, get_search_service  # noqa: E402
from src.services.cs_event_intel_service import (  # noqa: E402
    _EVENT_DIMENSION_ORDER,
    _balanced_event_items,
    _dicts_to_search_response,
    _fetch_hltv_crawl_items,
    _fetch_official_crawl_items,
)
from src.services.cs_item_intel_keywords import (  # noqa: E402
    build_cs_item_intel_keywords,
    resolve_item_containers,
    score_event_relevance,
)

_TIER_LABELS = {
    "direct": "本品相关",
    "case": "武器箱相关",
    "market": "市场要闻",
    "drop": "已过滤",
}

_DIM_LABELS = {
    "item_focus": "本品聚焦",
    "case_focus": "所属武器箱",
    "official_crawl": "官方博客(RSS)",
    "hltv_crawl": "HLTV(爬虫)",
    "official_update": "官方更新",
    "new_case": "新箱子",
    "cs_market": "饰品市场",
    "hltv": "HLTV(搜索)",
    "major_sticker": "Major/贴纸",
    "tieba": "贴吧",
}


def _resolve_item(*, good_id: int, item_query: str) -> Tuple[int, str, str]:
    client = CSQAQClient()
    if good_id:
        detail = client.get_item_good(good_id)
        goods = dict(detail.get("goods_info") or {})
        name = str(goods.get("name") or good_id).strip()
        market_hash = str(goods.get("market_hash_name") or good_id).strip()
        return int(good_id), name, market_hash

    entry = client.resolve_good_id(item_query, prefer_market_hash_name=item_query)
    return int(entry.id), str(entry.name), str(entry.market_hash_name)


def _collect_intel_results(
    *,
    good_id: int,
    item_name: str,
    market_hash_name: str,
    keywords,
    max_searches: int,
    search_days: int,
) -> Dict[str, SearchResponse]:
    cfg = get_config()
    intel_results: Dict[str, SearchResponse] = {}
    service = get_search_service()
    if service.is_available:
        intel_results = service.search_cs_event_intel(
            good_id=good_id,
            item_name=item_name,
            market_hash_name=market_hash_name,
            max_searches=max(1, int(max_searches)),
            search_days=search_days,
            case_labels=list(keywords.case_labels),
        )

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
    return intel_results


def _print_keywords(good_id: int, item_name: str, market_hash_name: str, containers: List[str]) -> None:
    print("=" * 72)
    print(f"good_id={good_id}")
    print(f"item_name={item_name}")
    print(f"market_hash_name={market_hash_name}")
    print(f"containers={', '.join(containers) if containers else '(无)'}")
    print("=" * 72)


def _print_result_row(
    *,
    tier: str,
    dimension: str,
    title: str,
    url: str,
    source: str,
    snippet: str,
    verbose: bool,
) -> None:
    if tier == "drop" and not verbose:
        return
    dim = _DIM_LABELS.get(dimension, dimension)
    label = _TIER_LABELS.get(tier, tier)
    print(f"[{label}] [{dim}] {title}")
    if source:
        print(f"  source={source}")
    if url:
        print(f"  url={url}")
    if snippet and verbose:
        print(f"  snippet={snippet[:180]}{'...' if len(snippet) > 180 else ''}")
    print()


def _audit_raw_results(
    intel_results: Dict[str, SearchResponse],
    keywords,
    *,
    verbose: bool,
) -> Dict[str, int]:
    counts = {"direct": 0, "case": 0, "market": 0, "drop": 0}
    print("\n--- 原始搜索结果（按维度） ---")
    for dimension in _EVENT_DIMENSION_ORDER:
        response = intel_results.get(dimension)
        if not response:
            continue
        dim = _DIM_LABELS.get(dimension, dimension)
        print(f"\n## {dim} | provider={response.provider} | query={response.query[:120]}")
        if not response.success or not response.results:
            print("  (无结果或搜索失败)")
            continue
        for result in response.results:
            tier = score_event_relevance(
                title=result.title or "",
                snippet=result.snippet or "",
                dimension=dimension,
                keywords=keywords,
            )
            counts[tier] += 1
            _print_result_row(
                tier=tier,
                dimension=dimension,
                title=(result.title or result.url or "").strip(),
                url=(result.url or "").strip(),
                source=(result.source or "").strip(),
                snippet=(result.snippet or "").strip(),
                verbose=verbose,
            )
    return counts


def _print_final_items(items: List[Dict[str, Any]]) -> None:
    print("\n--- 最终展示列表（与分析页一致） ---")
    if not items:
        print("  (空) — 搜不到本品/武器箱新闻属正常，可查看上方 market 条目或放宽配置")
        return
    for idx, row in enumerate(items, 1):
        tier = str(row.get("relevance") or "market")
        dim = _DIM_LABELS.get(str(row.get("dimension") or ""), row.get("dimension"))
        print(f"{idx}. [{_TIER_LABELS.get(tier, tier)}] [{dim}] {row.get('title')}")
        if row.get("url"):
            print(f"   {row.get('url')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe CS event intel relevance for one item")
    parser.add_argument("--good-id", type=int, default=769, help="CSQAQ good_id (default: 769)")
    parser.add_argument("--item", default="", help="Item query when good-id is omitted")
    parser.add_argument("--max-searches", type=int, default=0, help="Override CS_EVENT_INTEL_MAX_SEARCHES")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show dropped hits and snippets")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    cfg = get_config()
    if not getattr(cfg, "cs_event_intel_enabled", True):
        print("WARN: CS_EVENT_INTEL_ENABLED=false，请在 .env 中开启后再测")
        return 1

    service = get_search_service()
    if not service.is_available:
        print("WARN: 搜索 API 未配置（如 TAVILY_API_KEYS），将只能测 RSS/HLTV 爬虫源")

    try:
        good_id, item_name, market_hash_name = _resolve_item(
            good_id=args.good_id if args.good_id else 0,
            item_query=args.item.strip(),
        )
    except Exception as exc:
        print(f"ERROR: 无法解析饰品: {exc}")
        return 1

    containers = resolve_item_containers(good_id)
    _print_keywords(good_id, item_name, market_hash_name, containers)
    keywords = build_cs_item_intel_keywords(
        item_name=item_name,
        market_hash_name=market_hash_name,
        good_id=good_id,
        container_names=containers,
    )
    print(f"direct_keywords={sorted(keywords.direct)[:12]}{'...' if len(keywords.direct) > 12 else ''}")
    print(f"case_keywords={sorted(keywords.cases) if keywords.cases else '(无)'}")

    max_searches = args.max_searches or getattr(cfg, "cs_event_intel_max_searches", 8)
    profile = getattr(cfg, "cs_news_strategy_profile", "medium")
    search_days = resolve_news_window_days(cfg.news_max_age_days, profile)
    print(f"search_days={search_days} max_searches={max_searches}")

    intel_results = _collect_intel_results(
        good_id=good_id,
        item_name=item_name,
        market_hash_name=market_hash_name,
        keywords=keywords,
        max_searches=max_searches,
        search_days=search_days,
    )
    if not intel_results:
        print("ERROR: 无任何情报源结果")
        return 1

    counts = _audit_raw_results(intel_results, keywords, verbose=args.verbose)
    items = _balanced_event_items(intel_results, keywords)
    _print_final_items(items)

    direct_n = sum(1 for i in items if i.get("relevance") == "direct")
    case_n = sum(1 for i in items if i.get("relevance") == "case")
    market_n = sum(1 for i in items if i.get("relevance") == "market")
    print("\n--- 汇总 ---")
    print(f"原始命中: direct={counts['direct']} case={counts['case']} market={counts['market']} drop={counts['drop']}")
    print(f"最终展示: direct={direct_n} case={case_n} market={market_n} total={len(items)}")
    print("\n如何判断相关度：")
    print("  - direct：标题/摘要出现武器名、皮肤名（如 FAMAS / 机械工业）")
    print("  - case：出现所属武器箱名（如 手套武器箱 / glove case）")
    print("  - market：Major、Valve 更新、CS2 市场类；HLTV 纯战队续约应为 drop")
    if direct_n == 0:
        print("  - 无 direct 很常见；重点看 case/market 是否仍与 CS2 经济相关")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
