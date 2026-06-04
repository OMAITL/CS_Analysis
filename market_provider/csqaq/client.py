# -*- coding: utf-8 -*-
"""Thin client for CSQAQ Open API (https://docs.csqaq.com/)."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import requests

from market_provider.csqaq.cache import CSQAQCacheStore
from market_provider.csqaq.schemas import (
    CSQAQChartSeries,
    CSQAQPlatform,
    CSQAQResponse,
    GoodIdEntry,
    GoodIdSearchResult,
    IndexKlineBar,
    IndexKlinePeriod,
    ChartMetricKey,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.csqaq.com"
DEFAULT_MIN_INTERVAL_SECONDS = 1.2
DEFAULT_MAX_RETRIES = 3
DEFAULT_PRICE_PLATFORM = CSQAQPlatform.YYYP

_PLATFORM_ALIASES: Dict[str, CSQAQPlatform] = {
    "buff": CSQAQPlatform.BUFF,
    "1": CSQAQPlatform.BUFF,
    "yyyp": CSQAQPlatform.YYYP,
    "悠悠有品": CSQAQPlatform.YYYP,
    "悠悠": CSQAQPlatform.YYYP,
    "2": CSQAQPlatform.YYYP,
    "steam": CSQAQPlatform.STEAM,
    "3": CSQAQPlatform.STEAM,
}


def resolve_price_platform(value: Optional[Union[str, int, CSQAQPlatform]] = None) -> CSQAQPlatform:
    """
    Resolve the primary CS item price platform.

    Defaults to 悠悠有品 (YYYP) for decision-grade OHLCV. Override via
    ``CSQAQ_PRICE_PLATFORM`` (buff | yyyp | steam, or 1/2/3).
    """
    if isinstance(value, CSQAQPlatform):
        return value
    raw = (
        str(value).strip().lower()
        if value is not None
        else os.getenv("CSQAQ_PRICE_PLATFORM", "yyyp").strip().lower()
    )
    if not raw:
        return DEFAULT_PRICE_PLATFORM
    if raw in _PLATFORM_ALIASES:
        return _PLATFORM_ALIASES[raw]
    try:
        return CSQAQPlatform(int(raw))
    except (ValueError, KeyError) as exc:
        raise ValueError(
            f"Unknown CSQAQ price platform: {value!r}. Use buff, yyyp, steam, or 1/2/3."
        ) from exc


class CSQAQAPIError(RuntimeError):
    """Raised when CSQAQ returns a non-success business code."""

    def __init__(self, message: str, *, code: Optional[int] = None) -> None:
        super().__init__(message)
        self.code = code


class _RateLimiter:
    """Thread-safe minimum-interval gate (CSQAQ public limit: 1 req/s/IP)."""

    def __init__(self, min_interval_seconds: float = DEFAULT_MIN_INTERVAL_SECONDS) -> None:
        self._min_interval = max(0.0, float(min_interval_seconds))
        self._lock = threading.Lock()
        self._last_request_finished_at = 0.0

    def wait(self) -> None:
        if self._min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_finished_at
            if self._last_request_finished_at > 0 and elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)

    def mark_finished(self) -> None:
        with self._lock:
            self._last_request_finished_at = time.monotonic()

    @property
    def min_interval(self) -> float:
        return self._min_interval


class CSQAQClient:
    """
    Synchronous CSQAQ API client with built-in rate limiting and optional cache.

    Environment:
        CSQAQ_API_TOKEN  – required ApiToken header value
        CSQAQ_BASE_URL   – override API host (default https://api.csqaq.com)
        CSQAQ_MIN_INTERVAL_SECONDS – override 1 req/s gate (default 1.2s buffer)
        CSQAQ_MAX_RETRIES         – retries on HTTP 429/503 (default 3)
        CSQAQ_CACHE_DB   – SQLite cache path (see CSQAQCacheStore)
        CSQAQ_PRICE_PLATFORM – primary chart platform (default yyyp / 悠悠有品)
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        timeout: float = 30.0,
        min_interval_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        cache: Optional[CSQAQCacheStore] = None,
        enable_cache: bool = True,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_token = (api_token or os.getenv("CSQAQ_API_TOKEN", "")).strip()
        if not self.api_token:
            raise ValueError("CSQAQ_API_TOKEN is required")
        self.base_url = (base_url or os.getenv("CSQAQ_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout
        interval = min_interval_seconds
        if interval is None:
            raw = os.getenv("CSQAQ_MIN_INTERVAL_SECONDS", "")
            interval = float(raw) if raw else DEFAULT_MIN_INTERVAL_SECONDS
        self._rate_limiter = _RateLimiter(interval)
        retry_raw = os.getenv("CSQAQ_MAX_RETRIES", "")
        if max_retries is not None:
            self._max_retries = max(0, int(max_retries))
        elif retry_raw:
            self._max_retries = max(0, int(retry_raw))
        else:
            self._max_retries = DEFAULT_MAX_RETRIES
        self._session = session or requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        self.cache = cache if cache is not None else (CSQAQCacheStore() if enable_cache else None)

    def _cache_get_json(self, cache_key: str) -> Optional[Any]:
        if self.cache is None:
            return None
        raw = self.cache.get(cache_key)
        if raw is None:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Invalid CSQAQ cache payload for key=%s", cache_key)
            self.cache.invalidate(cache_key)
            return None

    def _cache_put_json(self, cache_key: str, payload: Any, ttl_seconds: int = 3600) -> None:
        if self.cache is None:
            return
        self.cache.put(cache_key, json.dumps(payload, ensure_ascii=False).encode("utf-8"), ttl_seconds)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
    ) -> Any:
        if cache_key:
            cached = self._cache_get_json(cache_key)
            if cached is not None:
                logger.debug("CSQAQ cache hit: %s", cache_key)
                return cached

        url = f"{self.base_url}{path}"
        headers = {"ApiToken": self.api_token}
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            self._rate_limiter.wait()
            try:
                resp = self._session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=self.timeout,
                )
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    sleep_seconds = float(retry_after) if retry_after else self._rate_limiter.min_interval * (attempt + 2)
                    logger.warning(
                        "CSQAQ rate limited (429) on %s %s; retry in %.1fs (attempt %d/%d)",
                        method,
                        path,
                        sleep_seconds,
                        attempt + 1,
                        self._max_retries + 1,
                    )
                    time.sleep(sleep_seconds)
                    last_error = CSQAQAPIError("Too many requests (429)", code=429)
                    continue
                if resp.status_code == 503:
                    sleep_seconds = self._rate_limiter.min_interval * (attempt + 2)
                    logger.warning(
                        "CSQAQ gateway busy (503) on %s %s; retry in %.1fs",
                        method,
                        path,
                        sleep_seconds,
                    )
                    time.sleep(sleep_seconds)
                    last_error = CSQAQAPIError("Service unavailable (503)", code=503)
                    continue
                resp.raise_for_status()
                envelope = CSQAQResponse.model_validate(resp.json())
                if envelope.code == 429:
                    sleep_seconds = self._rate_limiter.min_interval * (attempt + 2)
                    logger.warning("CSQAQ business code 429 on %s %s; retry in %.1fs", method, path, sleep_seconds)
                    time.sleep(sleep_seconds)
                    last_error = CSQAQAPIError(envelope.msg or "Too many requests", code=429)
                    continue
                if envelope.code != 200:
                    raise CSQAQAPIError(envelope.msg or "CSQAQ API error", code=envelope.code)
                if cache_key is not None:
                    self._cache_put_json(cache_key, envelope.data, cache_ttl_seconds)
                return envelope.data
            finally:
                self._rate_limiter.mark_finished()

        if last_error is not None:
            raise last_error
        raise CSQAQAPIError("CSQAQ request failed after retries")

    @staticmethod
    def _parse_good_id_map(payload: Dict[str, Any]) -> List[GoodIdEntry]:
        raw_items = (payload or {}).get("data") or {}
        items: List[GoodIdEntry] = []
        if isinstance(raw_items, dict):
            for value in raw_items.values():
                if isinstance(value, dict):
                    items.append(GoodIdEntry.model_validate(value))
        return items

    def search_goods(
        self,
        search: str,
        *,
        page_index: int = 1,
        page_size: int = 20,
    ) -> GoodIdSearchResult:
        """POST /api/v1/info/get_good_id – fuzzy search by CN/EN item name."""
        body = {"page_index": page_index, "page_size": page_size, "search": search}
        cache_key = f"good_id:{page_index}:{page_size}:{search}"
        data = self._request(
            "POST",
            "/api/v1/info/get_good_id",
            json_body=body,
            cache_key=cache_key,
            cache_ttl_seconds=86400,
        )
        items = self._parse_good_id_map(data or {})
        return GoodIdSearchResult(
            items=items,
            page_index=int((data or {}).get("page_index") or page_index),
            page_size=int((data or {}).get("page_size") or page_size),
            total=int((data or {}).get("total") or len(items)),
        )

    def resolve_good_id(
        self,
        query: str,
        *,
        prefer_market_hash_name: Optional[str] = None,
    ) -> GoodIdEntry:
        """
        Resolve a single good_id from a human query or market hash name.

        Raises:
            CSQAQAPIError: when no matching item is found.
        """
        result = self.search_goods(query, page_size=50)
        if not result.items:
            raise CSQAQAPIError(f"No CS item matched query: {query}")

        if prefer_market_hash_name:
            target = prefer_market_hash_name.strip()
            for item in result.items:
                if item.market_hash_name == target:
                    return item

        normalized_query = query.strip().lower()
        for item in result.items:
            if item.market_hash_name.lower() == normalized_query:
                return item
            if item.name.strip().lower() == normalized_query:
                return item

        if len(result.items) == 1:
            return result.items[0]
        raise CSQAQAPIError(
            f"Ambiguous CS item query '{query}'. "
            f"Pass prefer_market_hash_name or refine search. "
            f"Candidates: {[i.market_hash_name for i in result.items[:5]]}"
        )

    def get_item_chart(
        self,
        good_id: int,
        *,
        key: ChartMetricKey = "sell_price",
        platform: Optional[CSQAQPlatform] = None,
        period: int = 365,
        style: str = "all_style",
    ) -> CSQAQChartSeries:
        """POST /api/v1/info/chart – single-metric time series for one item."""
        resolved_platform = resolve_price_platform(platform)
        body = {
            "good_id": good_id,
            "key": key,
            "platform": int(resolved_platform),
            "period": period,
            "style": style,
        }
        cache_key = f"chart:{good_id}:{key}:{resolved_platform}:{period}:{style}"
        data = self._request(
            "POST",
            "/api/v1/info/chart",
            json_body=body,
            cache_key=cache_key,
            cache_ttl_seconds=1800,
        )
        return CSQAQChartSeries.from_api_payload(
            good_id=good_id,
            key=key,
            platform=resolved_platform,
            period=period,
            style=style,
            payload=data or {},
        )

    def get_item_daily_ohlcv_inputs(
        self,
        good_id: int,
        *,
        price_platform: Optional[CSQAQPlatform] = None,
        period: int = 365,
        style: str = "all_style",
        include_turnover_volume: bool = True,
    ) -> Dict[str, CSQAQChartSeries]:
        """
        Fetch price series and optional turnover volume for OHLCV building.

        Primary platform defaults to 悠悠有品 (YYYP); BUFF data is not merged here.

        Returns:
            dict with keys ``price`` and optionally ``volume``.
        """
        platform = resolve_price_platform(price_platform)
        price = self.get_item_chart(
            good_id,
            key="sell_price",
            platform=platform,
            period=period,
            style=style,
        )
        payload: Dict[str, CSQAQChartSeries] = {"price": price}
        if include_turnover_volume:
            try:
                payload["volume"] = self.get_item_chart(
                    good_id,
                    key="turnover_number",
                    platform=platform,
                    period=period,
                    style=style,
                )
            except CSQAQAPIError as exc:
                logger.info(
                    "CSQAQ turnover_number unavailable on %s for good_id=%s (code=%s); "
                    "OHLCV will fall back to sell_num or zero volume",
                    platform.name,
                    good_id,
                    exc.code,
                )
        return payload

    def get_index_kline(
        self,
        sub_index_id: str = "1",
        *,
        period: IndexKlinePeriod = "1day",
    ) -> List[IndexKlineBar]:
        """GET /api/v1/sub/kline – native index OHLCV bars."""
        params = {"id": sub_index_id, "type": period}
        cache_key = f"index_kline:{sub_index_id}:{period}"
        data = self._request(
            "GET",
            "/api/v1/sub/kline",
            params=params,
            cache_key=cache_key,
            cache_ttl_seconds=1800,
        )
        rows = list(data or [])
        return [IndexKlineBar.from_api_row(row) for row in rows if isinstance(row, dict)]

    def get_current_data(self, data_type: str = "init") -> Dict[str, Any]:
        """GET /api/v1/current_data – CSQAQ home dashboard payload."""
        cache_key = f"current_data:{data_type}"
        data = self._request(
            "GET",
            "/api/v1/current_data",
            params={"type": data_type},
            cache_key=cache_key,
            cache_ttl_seconds=600,
        )
        return dict(data or {})

    def list_sub_indexes(self, *, data_type: str = "init") -> List[Dict[str, Any]]:
        """Return ``sub_index_data`` rows from the home dashboard API."""
        payload = self.get_current_data(data_type)
        rows = payload.get("sub_index_data") or []
        return [dict(row) for row in rows if isinstance(row, dict)]

    def get_sub_data(self, sub_index_id: str, *, data_type: str = "daily") -> Dict[str, Any]:
        """GET /api/v1/sub_data – index detail time series."""
        cache_key = f"sub_data:{sub_index_id}:{data_type}"
        data = self._request(
            "GET",
            "/api/v1/sub_data",
            params={"id": sub_index_id, "type": data_type},
            cache_key=cache_key,
            cache_ttl_seconds=1800,
        )
        return dict(data or {})

    def get_page_list(
        self,
        *,
        page_index: int = 1,
        page_size: int = 100,
        search: str = "",
        filter_obj: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/info/get_page_list – paginated item catalog."""
        body: Dict[str, Any] = {
            "page_index": max(1, int(page_index)),
            "page_size": max(1, min(500, int(page_size))),
        }
        if search.strip():
            body["search"] = search.strip()
        if filter_obj:
            body["filter"] = filter_obj
        cache_key = f"page_list:{page_index}:{page_size}:{search}:{json.dumps(filter_obj or {}, sort_keys=True)}"
        data = self._request(
            "POST",
            "/api/v1/info/get_page_list",
            json_body=body,
            cache_key=cache_key,
            cache_ttl_seconds=3600,
        )
        return dict(data or {})

    def iter_page_list_items(
        self,
        *,
        page_size: int = 100,
        search: str = "",
        max_pages: Optional[int] = None,
    ):
        """Yield catalog rows across pages."""
        page_index = 1
        pages_fetched = 0
        while True:
            payload = self.get_page_list(
                page_index=page_index,
                page_size=page_size,
                search=search,
            )
            rows = list(payload.get("data") or [])
            if not rows:
                break
            for row in rows:
                if isinstance(row, dict):
                    yield row
            pages_fetched += 1
            if max_pages is not None and pages_fetched >= max_pages:
                break
            page_index += 1

    def get_item_good(self, good_id: int) -> Dict[str, Any]:
        """GET /api/v1/info/good – item detail snapshot including turnover_number."""
        cache_key = f"item_good:{good_id}"
        data = self._request(
            "GET",
            "/api/v1/info/good",
            params={"id": str(good_id)},
            cache_key=cache_key,
            cache_ttl_seconds=1800,
        )
        return dict(data or {})

    def get_item_kline_daily(
        self,
        good_id: int,
        *,
        platform: Optional[CSQAQPlatform] = None,
        max_time_ms: Optional[int] = None,
    ) -> List[IndexKlineBar]:
        """
        Try enterprise K-line (chartAll). Returns empty list when unavailable.
        """
        resolved = resolve_price_platform(platform)
        body: Dict[str, Any] = {
            "good_id": int(good_id),
            "plat": int(resolved),
            "periods": "1day",
            "max_time": int(max_time_ms or (time.time() * 1000)),
        }
        try:
            data = self._request(
                "POST",
                "/api/v1/info/simple/chartAll",
                json_body=body,
                cache_key=None,
            )
        except CSQAQAPIError as exc:
            logger.info("chartAll unavailable for good_id=%s (%s)", good_id, exc)
            return []
        except Exception as exc:
            logger.info("chartAll request failed for good_id=%s (%s)", good_id, exc)
            return []
        rows = list(data or [])
        bars: List[IndexKlineBar] = []
        for row in rows:
            if isinstance(row, dict) and "o" in row:
                bars.append(IndexKlineBar.from_api_row(row))
        return bars

    def build_cache_key_preview(self, **parts: Any) -> str:
        """Utility for tests/logging – stable cache key materialization."""
        encoded = urlencode(sorted((str(k), str(v)) for k, v in parts.items()))
        return encoded
