# -*- coding: utf-8 -*-
"""Polite HTTP client for HLTV (rate-limited, identifiable User-Agent)."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://www.hltv.org"
DEFAULT_MIN_INTERVAL = 2.0
DEFAULT_TIMEOUT = 20.0
DEFAULT_USER_AGENT = (
    "DSA-CS-Research/1.0 (personal CS2 market analysis; +https://github.com)"
)


class HLTVClient:
    """Minimal GET client with per-host rate limiting."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        min_interval_seconds: Optional[float] = None,
        timeout: Optional[float] = None,
        user_agent: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("HLTV_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        raw_interval = min_interval_seconds
        if raw_interval is None:
            raw_interval = float(os.getenv("HLTV_MIN_INTERVAL_SECONDS", str(DEFAULT_MIN_INTERVAL)))
        self.min_interval = max(1.0, float(raw_interval))
        self.timeout = float(timeout or os.getenv("HLTV_REQUEST_TIMEOUT", str(DEFAULT_TIMEOUT)))
        self.user_agent = (user_agent or os.getenv("HLTV_USER_AGENT", DEFAULT_USER_AGENT)).strip()
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/xml,text/html;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self._last_request_at = 0.0

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def get_text(self, path_or_url: str) -> str:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}{path_or_url}"
        self._wait()
        logger.debug("HLTV GET %s", url)
        resp = self._session.get(url, timeout=self.timeout)
        self._last_request_at = time.monotonic()
        resp.raise_for_status()
        return resp.text
