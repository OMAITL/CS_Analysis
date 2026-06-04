#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI: fetch recent HLTV news (sitemap / index fallback)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from crawlers.hltv import fetch_hltv_news  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch recent HLTV news")
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument("--max-age-days", type=int, default=14)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    import logging

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    items = fetch_hltv_news(max_items=args.max_items, max_age_days=args.max_age_days, fail_soft=False)
    if not items:
        print("No HLTV news items returned.")
        return 1
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.title}")
        print(f"   {item.url}")
        if item.published_date:
            print(f"   {item.published_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
