# -*- coding: utf-8 -*-
"""Unified item data provider for CS chat pipeline."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


@dataclass
class ItemDataBundle:
    """Normalized data bundle for skill engine + LLM narrator."""

    good_id: Optional[int] = None
    item_info: Dict[str, Any] = field(default_factory=dict)
    price_history: List[Dict[str, Any]] = field(default_factory=list)
    volume_history: List[Dict[str, Any]] = field(default_factory=list)
    listing_history: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    trend: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "good_id": self.good_id,
            "item_info": self.item_info,
            "price_history": self.price_history[-30:],
            "volume_history": self.volume_history[-30:],
            "listing_history": self.listing_history,
            "events": self.events[:8],
            "trend": self.trend,
            "meta": self.meta,
            "error": self.error,
        }


class ItemDataProvider:
    """Fetch fused CS item data from crawl DB, CSQAQ API, and event intel."""

    def __init__(self) -> None:
        self.crawl_pages = _env_int("CS_CHAT_CRAWL_BACKFILL_PAGES", 5)

    def fetch(
        self,
        *,
        good_id: Optional[int] = None,
        item: Optional[str] = None,
        platform: Optional[str] = None,
        period: int = 180,
        prefer_crawl: bool = True,
        refresh_today: bool = True,
        refresh_crawl: bool = False,
        kline_pages: Optional[int] = None,
    ) -> ItemDataBundle:
        return self._fetch_once(
            good_id=good_id,
            item=item,
            platform=platform,
            period=period,
            prefer_crawl=prefer_crawl,
            refresh_today=refresh_today,
            refresh_crawl=refresh_crawl,
            kline_pages=kline_pages or 2,
        )

    def fetch_with_backfill(
        self,
        *,
        good_id: Optional[int] = None,
        item: Optional[str] = None,
        platform: Optional[str] = None,
        period: int = 180,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> ItemDataBundle:
        """
        Fetch item data; when local/API OHLCV is missing, trigger Playwright K-line crawl and retry.
        """
        bundle = self._fetch_once(
            good_id=good_id,
            item=item,
            platform=platform,
            period=period,
            prefer_crawl=True,
            refresh_crawl=False,
            refresh_today=True,
            kline_pages=2,
        )
        if not self._needs_crawl_backfill(bundle):
            return bundle

        if progress_callback:
            progress_callback(
                {
                    "type": "generating",
                    "message": "本地无 K 线数据，正在爬取饰品行情（K 线/成交量）…",
                }
            )
        logger.info(
            "ItemDataProvider crawl backfill good_id=%s item=%r crawl_rows=%s api_rows=%s",
            good_id,
            item,
            (bundle.meta or {}).get("crawl_rows"),
            (bundle.meta or {}).get("api_rows"),
        )

        crawled = self._fetch_once(
            good_id=good_id,
            item=item,
            platform=platform,
            period=period,
            prefer_crawl=True,
            refresh_crawl=True,
            refresh_today=False,
            kline_pages=self.crawl_pages,
        )
        crawled.meta = dict(crawled.meta or {})
        crawled.meta["crawl_backfill"] = True
        crawled.meta["crawl_backfill_pages"] = self.crawl_pages

        if self._needs_crawl_backfill(crawled) and not crawled.error:
            crawled.meta["crawl_backfill_status"] = "partial"
        elif crawled.error:
            crawled.meta["crawl_backfill_status"] = "failed"
        else:
            crawled.meta["crawl_backfill_status"] = "ok"
        return crawled

    @staticmethod
    def _needs_crawl_backfill(bundle: ItemDataBundle) -> bool:
        if bundle.good_id is None and not bundle.item_info.get("good_id"):
            return False
        if bundle.error:
            lowered = bundle.error.lower()
            if "empty ohlcv" in lowered or "good_id" in lowered:
                return True
        if bundle.price_history:
            return False
        crawl_rows = int((bundle.meta or {}).get("crawl_rows") or 0)
        api_rows = int((bundle.meta or {}).get("api_rows") or 0)
        return crawl_rows == 0 and api_rows == 0

    def _fetch_once(
        self,
        *,
        good_id: Optional[int] = None,
        item: Optional[str] = None,
        platform: Optional[str] = None,
        period: int = 180,
        prefer_crawl: bool = True,
        refresh_today: bool = True,
        refresh_crawl: bool = False,
        kline_pages: int = 2,
    ) -> ItemDataBundle:
        if good_id is None and not (item or "").strip():
            return ItemDataBundle(error="good_id or item is required")

        try:
            from src.services.cs_item_service import CSItemService

            payload = CSItemService().analyze_item(
                good_id=good_id,
                item=item,
                platform=platform,
                period=period,
                prefer_crawl=prefer_crawl,
                refresh_crawl=refresh_crawl,
                refresh_today=refresh_today,
                kline_pages=kline_pages,
                include_report=False,
                skills=None,
                fallback_name=(item or "").strip(),
            )
        except Exception as exc:
            logger.warning("ItemDataProvider fetch failed: %s", exc)
            return ItemDataBundle(
                good_id=good_id,
                error=str(exc),
                item_info={"name": item or "", "good_id": good_id},
            )

        return self._payload_to_bundle(payload, good_id=good_id, item=item)

    @staticmethod
    def _payload_to_bundle(
        payload: Dict[str, Any],
        *,
        good_id: Optional[int] = None,
        item: Optional[str] = None,
    ) -> ItemDataBundle:
        snapshot = dict(payload.get("snapshot") or {})
        trend = dict(payload.get("trend") or {})
        ohlcv = list(payload.get("ohlcv") or [])
        meta = dict(payload.get("meta") or {})

        item_info = {
            "good_id": payload.get("good_id"),
            "name": payload.get("item_name") or snapshot.get("name"),
            "market_hash_name": payload.get("market_hash_name") or snapshot.get("market_hash_name"),
            "platform": payload.get("platform"),
            "buff_sell_price": snapshot.get("buff_sell_price"),
            "yyyp_sell_price": snapshot.get("yyyp_sell_price"),
            "steam_sell_price": snapshot.get("steam_sell_price"),
            "buff_sell_num": snapshot.get("buff_sell_num"),
            "yyyp_sell_num": snapshot.get("yyyp_sell_num"),
            "turnover_number": snapshot.get("turnover_number"),
            "data_sources": snapshot.get("data_sources"),
            "api_snapshot_error": snapshot.get("api_snapshot_error"),
        }

        price_history = [
            {
                "date": row.get("date"),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "change_percent": row.get("change_percent") or row.get("pct_chg"),
            }
            for row in ohlcv
        ]
        volume_history = [
            {
                "date": row.get("date"),
                "volume": row.get("volume"),
                "amount": row.get("amount"),
            }
            for row in ohlcv
        ]

        listing_history: List[Dict[str, Any]] = []
        if snapshot.get("yyyp_sell_num") is not None or snapshot.get("buff_sell_num") is not None:
            listing_history.append(
                {
                    "as_of": snapshot.get("updated_at") or "latest",
                    "yyyp_sell_num": snapshot.get("yyyp_sell_num"),
                    "buff_sell_num": snapshot.get("buff_sell_num"),
                }
            )

        return ItemDataBundle(
            good_id=int(payload.get("good_id") or good_id or 0) or None,
            item_info=item_info,
            price_history=price_history,
            volume_history=volume_history,
            listing_history=listing_history,
            events=list(payload.get("event_intel") or []),
            trend=trend,
            meta={
                "data_quality": meta.get("data_quality"),
                "crawl_rows": meta.get("crawl_rows"),
                "api_rows": meta.get("api_rows"),
                "ohlc_source": meta.get("ohlc_source"),
                "volume_source": meta.get("volume_source"),
            },
        )
