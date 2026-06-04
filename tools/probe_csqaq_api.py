#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe CSQAQ endpoints to verify API token, URL and platform metrics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from market_provider.csqaq import CSQAQAPIError, CSQAQClient  # noqa: E402
from market_provider.csqaq.schemas import CSQAQPlatform  # noqa: E402


def _print_public_ip_hint() -> None:
    try:
        import urllib.request

        ip = urllib.request.urlopen("https://api.ipify.org", timeout=8).read().decode().strip()
        print(f"public_ip={ip}  (add this to CSQAQ API whitelist if you get 401)")
    except Exception as exc:
        print(f"public_ip=unknown ({exc}); open https://api.ipify.org in browser")


def _print_http_error_hints(exc: Exception) -> None:
    import requests

    if not isinstance(exc, requests.HTTPError) or exc.response is None:
        return
    status = exc.response.status_code
    body = (exc.response.text or "").strip()[:400]
    if body:
        print(f"response_body={body}")
    if status == 401:
        print(
            "401 hints: (1) ApiToken in .env must match CSQAQ user center exactly; "
            "(2) whitelist must include your current public IP (see public_ip above); "
            "(3) restart uvicorn after editing .env"
        )
    elif status == 429:
        print("429 hints: wait 1-2 minutes; CSQAQ limits ~1 req/s (CSQAQ_MIN_INTERVAL_SECONDS=1.2)")


def _probe(name: str, fn) -> bool:
    try:
        result = fn()
        if hasattr(result, "items"):
            print(f"OK  {name}: items={len(result.items)} total={result.total}")
        else:
            points = len(result.timestamps)
            print(f"OK  {name}: points={points} platform={result.platform.name}")
        return True
    except CSQAQAPIError as exc:
        print(f"ERR {name}: business_code={exc.code} msg={exc}")
        return False
    except Exception as exc:
        print(f"ERR {name}: {type(exc).__name__}: {exc}")
        return False


def main() -> int:
    import os

    token = os.getenv("CSQAQ_API_TOKEN", "").strip()
    base = os.getenv("CSQAQ_BASE_URL", "https://api.csqaq.com")
    print(f"base_url={base}")
    print(f"token_set={'yes' if token else 'no'} (len={len(token)})")
    print(f"price_platform={os.getenv('CSQAQ_PRICE_PLATFORM', 'yyyp')}")
    _print_public_ip_hint()
    print("-" * 60)

    client = CSQAQClient(enable_cache=False)
    try:
        search = client.search_goods("AK-47 | Redline (Field-Tested)", page_size=5)
    except Exception as exc:
        print(f"ERR search: {type(exc).__name__}: {exc}")
        _print_http_error_hints(exc)
        return 1
    if not search.items:
        print("ERR search: no items matched")
        return 1
    entry = search.items[0]
    good_id = entry.id
    print(f"OK  search: good_id={good_id} name={entry.name}")
    print("-" * 60)

    checks = [
        ("sell_price / YYYP", lambda: client.get_item_chart(good_id, key="sell_price", platform=CSQAQPlatform.YYYP, period=30)),
        ("sell_price / BUFF", lambda: client.get_item_chart(good_id, key="sell_price", platform=CSQAQPlatform.BUFF, period=30)),
        ("turnover_number / YYYP", lambda: client.get_item_chart(good_id, key="turnover_number", platform=CSQAQPlatform.YYYP, period=30)),
        ("turnover_number / BUFF", lambda: client.get_item_chart(good_id, key="turnover_number", platform=CSQAQPlatform.BUFF, period=30)),
        ("turnover_number / STEAM", lambda: client.get_item_chart(good_id, key="turnover_number", platform=CSQAQPlatform.STEAM, period=30)),
    ]
    ok_count = 0
    for name, fn in checks:
        if _probe(name, fn):
            ok_count += 1

    print("-" * 60)
    print(f"passed {ok_count}/{len(checks)} chart probes")
    return 0 if ok_count >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
