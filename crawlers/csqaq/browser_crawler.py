# -*- coding: utf-8 -*-
"""CSQAQ volume crawler – Playwright K-line chartAll capture for csqaq.com."""

from __future__ import annotations

import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from zoneinfo import ZoneInfo

import pandas as pd

from market_provider.csqaq.client import resolve_price_platform
from market_provider.csqaq.ohlcv_adapter import ms_to_market_date_iso
from market_provider.csqaq.schemas import CSQAQPlatform, IndexKlineBar

logger = logging.getLogger(__name__)

CSQAQ_HOME_URL = "https://csqaq.com/home"
CSQAQ_RANK_URL = "https://csqaq.com/rank"
CHART_ALL_ROUTE = "**/info/simple/chartAll"
_RANK_DAY_LABELS = {1: "近1天", 7: "近7天", 30: "近30天", 180: "近180天"}
_MARKET_TZ = ZoneInfo("Asia/Shanghai")

T = TypeVar("T")


def _run_playwright_isolated(func: Callable[[], T]) -> T:
    """
    Run sync Playwright in a dedicated worker thread.

    Uvicorn/FastAPI worker threads on Windows may use SelectorEventLoop, where
    Playwright cannot spawn browser subprocesses (NotImplementedError).
    """

    def _runner() -> T:
        if sys.platform == "win32":
            import asyncio

            policy = asyncio.WindowsProactorEventLoopPolicy()
            asyncio.set_event_loop_policy(policy)
            asyncio.set_event_loop(policy.new_event_loop())
        return func()

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="csqaq-playwright") as pool:
        return pool.submit(_runner).result()


def _default_max_time_ms() -> int:
    """Request bars through tomorrow 00:00 market time (matches csqaq.com default)."""
    now = datetime.now(_MARKET_TZ)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int(tomorrow.timestamp() * 1000)


class CSQAQBrowserCrawler:
    """
    Capture K-line OHLCV (field ``v`` = 成交量) from CSQAQ goods pages.

    The open API cannot return chartAll volume on free tokens; the website proxy
    endpoint works when triggered from a real browser session. This crawler uses
    Playwright route interception to select platform (BUFF/YYYP) and paginate
    history (150 bars per request).

    Requires: ``pip install playwright`` and ``python -m playwright install chromium``.
    """

    def __init__(self, *, headless: bool = True, timeout_ms: int = 120_000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms

    @staticmethod
    def _trigger_kline_mode(page) -> None:
        """Click chart controls until the site loads the K-line (chartAll) view."""
        for label in ("K线", "切换", "常规", "切换常规图"):
            locator = page.get_by_text(label, exact=False)
            if locator.count() == 0:
                continue
            try:
                locator.first.click(timeout=2500)
                page.wait_for_timeout(1800)
            except Exception:
                pass
        for selector in ("text=日线",):
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            try:
                locator.first.click(timeout=2500)
                page.wait_for_timeout(1800)
                break
            except Exception:
                pass

    def crawl_item_kline_volume(
        self,
        good_id: int,
        *,
        platform: Optional[Union[str, int, CSQAQPlatform]] = None,
        max_pages: int = 5,
        periods: str = "1day",
        item_name: Optional[str] = None,
        market_hash_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Crawl daily K-line volume (``v``) for one item from ``/goods/{good_id}``.

        Returns rows with ``volume_source=kline_chart_all_v`` – the same metric shown
        in the website K-line tooltip (成交量), not listing count (``sell_num``).
        """
        resolved = resolve_price_platform(platform)
        plat = int(resolved.value)
        platform_name = resolved.name.lower()
        goods_url = f"https://csqaq.com/goods/{int(good_id)}"

        def _crawl() -> pd.DataFrame:
            from playwright.sync_api import sync_playwright

            route_state: Dict[str, int] = {"max_time": _default_max_time_ms(), "plat": plat}
            bars_by_ts: Dict[str, Dict[str, Any]] = {}
            pages_received = 0

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                page = browser.new_page(viewport={"width": 1600, "height": 1000})

                def handle_route(route, request) -> None:
                    if "chartAll" not in request.url:
                        route.continue_()
                        return
                    payload = {
                        "good_id": int(good_id),
                        "plat": route_state["plat"],
                        "periods": periods,
                        "max_time": route_state["max_time"],
                    }
                    route.continue_(post_data=json.dumps(payload))

                page.route(CHART_ALL_ROUTE, handle_route)

                def on_response(resp) -> None:
                    nonlocal pages_received
                    if "chartAll" not in resp.url or resp.status != 200:
                        return
                    try:
                        body = resp.json()
                    except Exception:
                        return
                    data = body.get("data") or []
                    if not isinstance(data, list) or not data:
                        return
                    pages_received += 1
                    for item in data:
                        if not isinstance(item, dict) or "t" not in item:
                            continue
                        ts = str(item["t"])
                        bar = IndexKlineBar.from_api_row(item)
                        bars_by_ts[ts] = {
                            "good_id": int(good_id),
                            "item_name": item_name or good_id,
                            "market_hash_name": market_hash_name or good_id,
                            "platform": platform_name,
                            "date": ms_to_market_date_iso(bar.timestamp_ms),
                            "volume": float(bar.volume),
                            "open": float(bar.open),
                            "high": float(bar.high),
                            "low": float(bar.low),
                            "close": float(bar.close),
                            "volume_source": "kline_chart_all_v",
                        }
                    route_state["max_time"] = int(data[0]["t"]) - 1

                page.on("response", on_response)
                page.goto(goods_url, wait_until="networkidle", timeout=self.timeout_ms)
                page.wait_for_timeout(3000)

                for page_idx in range(max(1, max_pages)):
                    attempts = 0
                    while pages_received <= page_idx and attempts < 3:
                        self._trigger_kline_mode(page)
                        page.wait_for_timeout(4500)
                        attempts += 1
                    if pages_received <= page_idx:
                        logger.debug(
                            "good_id=%s plat=%s stopped pagination at page=%s (received=%s)",
                            good_id,
                            platform_name,
                            page_idx,
                            pages_received,
                        )
                        break

                browser.close()

            if not bars_by_ts:
                logger.warning("good_id=%s plat=%s no K-line volume captured", good_id, platform_name)
                return pd.DataFrame()

            rows = sorted(bars_by_ts.values(), key=lambda r: r["date"])
            logger.info(
                "good_id=%s plat=%s captured %s daily bars (%s chartAll pages)",
                good_id,
                platform_name,
                len(rows),
                pages_received,
            )
            return pd.DataFrame(rows)

        return _run_playwright_isolated(_crawl)

    def crawl_home_index_kline(
        self,
        *,
        sub_index_id: str = "1",
        trigger_kline_tab: bool = True,
    ) -> pd.DataFrame:
        """
        Open https://csqaq.com/home and capture ``/sub/kline`` responses.

        Note: free tokens often return ``v=0`` on this endpoint; prefer item K-line
        crawler for decision-grade volume when possible.
        """
        captured: List[Dict[str, Any]] = []

        def _crawl() -> None:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                page = browser.new_page(viewport={"width": 1600, "height": 1000})

                def on_response(resp) -> None:
                    url = resp.url
                    if "/sub/kline" not in url or resp.status != 200:
                        return
                    if f"id={sub_index_id}" not in url:
                        return
                    try:
                        body = resp.json()
                    except Exception:
                        return
                    captured.append({"url": url, "body": body})

                page.on("response", on_response)
                page.goto(CSQAQ_HOME_URL, wait_until="networkidle", timeout=self.timeout_ms)
                page.wait_for_timeout(4000)
                if trigger_kline_tab:
                    for label in ("K线", "K"):
                        locator = page.get_by_text(label, exact=False)
                        if locator.count() > 0:
                            try:
                                locator.first.click(timeout=3000)
                                page.wait_for_timeout(4000)
                                break
                            except Exception:
                                pass
                browser.close()

        _run_playwright_isolated(_crawl)

        rows: List[Dict[str, Any]] = []
        for hit in captured:
            data = (hit.get("body") or {}).get("data") or []
            if not isinstance(data, list):
                continue
            for item in data:
                if not isinstance(item, dict):
                    continue
                bar = IndexKlineBar.from_api_row(item)
                rows.append(
                    {
                        "sub_index_id": str(sub_index_id),
                        "date": ms_to_market_date_iso(bar.timestamp_ms),
                        "volume": float(bar.volume),
                        "close": float(bar.close),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "volume_source": "browser_sub_kline_v",
                        "capture_url": hit.get("url"),
                    }
                )
        return pd.DataFrame(rows)

    def crawl_goods_page_charts(self, good_id: int, *, wait_ms: int = 12_000) -> pd.DataFrame:
        """Backward-compatible alias – use :meth:`crawl_item_kline_volume` instead."""
        return self.crawl_item_kline_volume(good_id, max_pages=1)

    @staticmethod
    def _rank_day_label(day_type: int) -> str:
        return _RANK_DAY_LABELS.get(int(day_type), f"近{int(day_type)}天")

    @staticmethod
    def _select_rank_day_range(page, day_type: int) -> None:
        """Open the rank-page day dropdown and pick ``近N天`` (default page load is 近1天)."""
        target = CSQAQBrowserCrawler._rank_day_label(day_type)
        if target == "近1天":
            return
        opened = False
        for opener in _RANK_DAY_LABELS.values():
            locator = page.get_by_text(opener, exact=True)
            if locator.count() == 0:
                continue
            try:
                locator.first.click(timeout=2500)
                page.wait_for_timeout(600)
                opened = True
                break
            except Exception:
                continue
        if not opened:
            return
        option = page.get_by_text(target, exact=True)
        if option.count() == 0:
            return
        try:
            option.first.click(timeout=3000)
            page.wait_for_timeout(3500)
        except Exception:
            pass

    @staticmethod
    def _pick_rank_payload(
        captured: List[tuple[str, Dict[str, Any]]],
        *,
        day_type: int,
        direction: str,
    ) -> Dict[str, Any]:
        day_token = CSQAQBrowserCrawler._rank_day_label(day_type)
        needle_up = "价格_价格上升"
        needle_down = "价格_价格下降"
        matches: List[Dict[str, Any]] = []
        for body, payload in captured:
            if day_token not in (body or ""):
                continue
            if direction == "up" and needle_up in body:
                matches.append(payload)
            elif direction == "down" and needle_down in body:
                matches.append(payload)
        return matches[-1] if matches else {}

    @staticmethod
    def _rank_rows_from_payload(payload: Dict[str, Any], *, limit: int) -> List[Dict[str, Any]]:
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return []
        rows = list(data.get("data") or [])
        return [dict(row) for row in rows[: max(1, int(limit))] if isinstance(row, dict)]

    def fetch_rank_leaders(
        self,
        *,
        day_type: int = 7,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Capture gain/loss rank tables from https://csqaq.com/rank via Playwright.

        The Open API ``get_rank_list`` often times out; the website proxy works when
        triggered from a real browser session on the rank page.
        """
        page_size = max(1, min(int(limit), 20))
        captured: List[tuple[str, Dict[str, Any]]] = []

        def _crawl() -> List[tuple[str, Dict[str, Any]]]:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                page = browser.new_page()

                def on_response(response) -> None:
                    if "get_rank_list" not in response.url or response.status != 200:
                        return
                    try:
                        payload = response.json()
                        if isinstance(payload, dict):
                            captured.append((response.request.post_data or "", payload))
                    except Exception:
                        pass

                page.on("response", on_response)
                page.goto(CSQAQ_RANK_URL, wait_until="networkidle", timeout=self.timeout_ms)
                page.wait_for_timeout(2500)
                self._select_rank_day_range(page, day_type)

                for label in ("跌幅榜(百分比)", "跌幅榜"):
                    locator = page.get_by_text(label, exact=False)
                    if locator.count() == 0:
                        continue
                    try:
                        locator.first.click(timeout=3000)
                        page.wait_for_timeout(3500)
                        break
                    except Exception:
                        pass

                browser.close()
                return captured

        _run_playwright_isolated(_crawl)

        gain_payload = self._pick_rank_payload(captured, day_type=day_type, direction="up")
        loss_payload = self._pick_rank_payload(captured, day_type=day_type, direction="down")
        return {
            "day_type": int(day_type),
            "limit": int(limit),
            "gainers": self._rank_rows_from_payload(gain_payload, limit=page_size),
            "losers": self._rank_rows_from_payload(loss_payload, limit=page_size),
            "source": "browser_rank_page",
        }

    def search_goods(self, query: str, *, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        Search items through csqaq.com same-origin API (works when Open API token returns 401).

        Uses Playwright to call ``/api/v1/info/get_good_id`` from the website origin.
        """
        term = (query or "").strip()
        if not term:
            return []

        payload = {
            "page_index": 1,
            "page_size": max(1, min(int(page_size), 50)),
            "search": term,
        }

        import os

        api_token = (os.getenv("CSQAQ_API_TOKEN") or "").strip()
        api_base = (os.getenv("CSQAQ_BASE_URL") or "https://api.csqaq.com").rstrip("/")
        api_url = f"{api_base}/api/v1/info/get_good_id"

        def _search() -> str:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                request = playwright.request.new_context(
                    extra_http_headers={
                        "ApiToken": api_token,
                        "Content-Type": "application/json",
                    }
                )
                resp = request.post(api_url, data=payload, timeout=self.timeout_ms)
                body = resp.text()
                request.dispose()
                return body

        body = _run_playwright_isolated(_search)

        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"browser get_good_id invalid JSON: {body[:200]}")

        if not isinstance(result, dict) or int(result.get("code") or 0) != 200:
            raise RuntimeError(f"browser get_good_id failed: {result}")

        raw_items = (result.get("data") or {})
        rows: List[Dict[str, Any]] = []
        if isinstance(raw_items, dict):
            for value in raw_items.values():
                if not isinstance(value, dict):
                    continue
                gid = value.get("id") if value.get("id") is not None else value.get("good_id")
                if gid is None:
                    continue
                rows.append(
                    {
                        "good_id": int(gid),
                        "name": str(value.get("name") or gid),
                        "market_hash_name": str(
                            value.get("market_hash_name") or value.get("marketHashName") or value.get("name") or gid
                        ),
                    }
                )
        return rows
