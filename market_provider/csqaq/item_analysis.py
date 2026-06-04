# -*- coding: utf-8 -*-
"""Run fused CS item analysis and collect context for reports."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

TODAY_KLINE_PAGES = 1

from crawlers.csqaq.browser_crawler import CSQAQBrowserCrawler
from crawlers.csqaq.store import VolumeCrawlStore
from market_provider.csqaq.analysis_store import CSAnalysisStore
from market_provider.csqaq.client import CSQAQClient, resolve_price_platform
from market_provider.csqaq.item_ohlcv_builder import ItemOhlcvBuilder
from market_provider.csqaq.schemas import CSQAQPlatform, GoodIdEntry, MergedItemOhlcvMeta
from src.stock_analyzer import StockTrendAnalyzer, TrendAnalysisResult


@dataclass
class CSItemAnalysisContext:
    """Structured inputs for CS item LLM / template reports."""

    good_id: int
    item_name: str
    market_hash_name: str
    platform: str
    snapshot: Dict[str, Any]
    meta: MergedItemOhlcvMeta
    trend: TrendAnalysisResult
    ohlcv_rows: List[Dict[str, Any]] = field(default_factory=list)
    ohlcv_tail: List[Dict[str, Any]] = field(default_factory=list)
    event_context: str = ""
    event_intel: List[Dict[str, Any]] = field(default_factory=list)


def fetch_item_snapshot(client: CSQAQClient, good_id: int) -> Dict[str, Any]:
    detail = client.get_item_good(good_id)
    goods = dict(detail.get("goods_info") or {})
    return goods


def refresh_item_kline_crawl(
    client: CSQAQClient,
    good_id: int,
    *,
    platform: Optional[Union[str, int, CSQAQPlatform]] = None,
    kline_pages: int = 5,
    fail_soft: bool = False,
) -> int:
    """
    Crawl K-line bars via Playwright and upsert into ``CSQAQ_CRAWL_DB``.

    When ``fail_soft`` is True (e.g. lightweight today refresh), errors are logged
    and ``0`` is returned instead of raising.
    """
    try:
        goods = fetch_item_snapshot(client, good_id)
        browser = CSQAQBrowserCrawler()
        frame = browser.crawl_item_kline_volume(
            good_id,
            platform=platform,
            max_pages=kline_pages,
            item_name=str(goods.get("name") or good_id),
            market_hash_name=str(goods.get("market_hash_name") or good_id),
        )
        if frame.empty:
            return 0
        return VolumeCrawlStore().upsert_item_rows(frame.to_dict(orient="records"))
    except Exception as exc:
        if fail_soft:
            logger.warning(
                "CS item kline refresh skipped (good_id=%s, pages=%s): %s",
                good_id,
                kline_pages,
                exc,
            )
            return 0
        raise


def run_cs_item_analysis(
    *,
    client: Optional[CSQAQClient] = None,
    good_id: Optional[int] = None,
    item_query: Optional[str] = None,
    platform: Optional[Union[str, int, CSQAQPlatform]] = None,
    period: int = 365,
    prefer_crawl: bool = True,
    refresh_crawl: bool = False,
    refresh_today: bool = True,
    kline_pages: int = 5,
    store_result: bool = True,
    ohlcv_tail_rows: int = 20,
) -> CSItemAnalysisContext:
    """
    Build fused OHLCV, run trend analysis, return report-ready context.

    Historical bars are read from crawl DB + API. When ``refresh_today`` is True
    (default) and ``refresh_crawl`` is False, a lightweight Playwright crawl
    (``TODAY_KLINE_PAGES``) refreshes the latest bars (including today) before merge.
    """
    api = client or CSQAQClient()
    resolved = resolve_price_platform(platform)
    platform_name = resolved.name.lower()

    entry: GoodIdEntry
    if good_id is not None:
        goods = fetch_item_snapshot(api, int(good_id))
        entry = GoodIdEntry(
            id=int(good_id),
            name=str(goods.get("name") or good_id),
            market_hash_name=str(goods.get("market_hash_name") or good_id),
        )
    elif item_query:
        entry = api.resolve_good_id(item_query, prefer_market_hash_name=item_query)
        good_id = entry.id
    else:
        raise ValueError("good_id or item_query is required")

    if refresh_crawl:
        refresh_item_kline_crawl(
            api,
            int(good_id),
            platform=resolved,
            kline_pages=kline_pages,
        )
    elif refresh_today:
        refresh_item_kline_crawl(
            api,
            int(good_id),
            platform=resolved,
            kline_pages=TODAY_KLINE_PAGES,
            fail_soft=True,
        )

    builder = ItemOhlcvBuilder(client=api)
    frame, meta = builder.build(
        int(good_id),
        entry=entry,
        platform=resolved,
        period=period,
        prefer_crawl=prefer_crawl,
    )
    if frame.empty:
        raise RuntimeError(f"good_id={good_id} produced empty OHLCV frame")

    if store_result:
        CSAnalysisStore().upsert_item_ohlcv_rows(frame.to_dict(orient="records"))

    trend_input = frame[["date", "open", "high", "low", "close", "volume", "amount", "pct_chg"]].copy()
    trend = StockTrendAnalyzer().analyze(trend_input, code=entry.market_hash_name)

    export_cols = [c for c in ["date", "open", "high", "low", "close", "volume", "amount", "pct_chg"] if c in frame.columns]
    ohlcv_rows = frame[export_cols].to_dict(orient="records")
    for row in ohlcv_rows:
        if hasattr(row.get("date"), "isoformat"):
            row["date"] = row["date"].isoformat()
    ohlcv_tail = ohlcv_rows[-max(1, ohlcv_tail_rows) :]

    snapshot = fetch_item_snapshot(api, int(good_id))
    return CSItemAnalysisContext(
        good_id=int(good_id),
        item_name=entry.name,
        market_hash_name=entry.market_hash_name,
        platform=platform_name,
        snapshot=snapshot,
        meta=meta,
        trend=trend,
        ohlcv_rows=ohlcv_rows,
        ohlcv_tail=ohlcv_tail,
    )
