#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crawl CSQAQ home index daily volume (https://csqaq.com/home)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

import pandas as pd  # noqa: E402

from crawlers.csqaq.api_crawler import CSQAQVolumeCrawler  # noqa: E402
from crawlers.csqaq.browser_crawler import CSQAQBrowserCrawler  # noqa: E402
from crawlers.csqaq.store import VolumeCrawlStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl CSQAQ index daily volume from home page indexes")
    parser.add_argument("--index-id", action="append", dest="index_ids", help="Sub index id (repeatable). Default: all from home")
    parser.add_argument("--csv", default="", help="Optional CSV export path")
    parser.add_argument("--browser", action="store_true", help="Also capture /sub/kline via Playwright on csqaq.com/home")
    parser.add_argument("--no-store", action="store_true", help="Skip SQLite persistence")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    api = CSQAQVolumeCrawler()
    index_ids = args.index_ids or None
    frame = api.crawl_home_index_volumes(index_ids=index_ids)
    if args.browser:
        browser = CSQAQBrowserCrawler()
        target_id = (args.index_ids or ["1"])[0]
        browser_frame = browser.crawl_home_index_kline(sub_index_id=str(target_id))
        if not browser_frame.empty:
            browser_frame["sub_index_name"] = browser_frame["sub_index_id"]
            frame = (
                pd.concat([frame, browser_frame], ignore_index=True)
                if not frame.empty
                else browser_frame
            )

    if frame.empty:
        print("No index volume rows captured.")
        return 1

    print(frame.tail(10).to_string(index=False))
    nonzero = int((frame["volume"] > 0).sum())
    print(f"\nrows={len(frame)} nonzero_volume={nonzero}")
    if nonzero == 0:
        print("NOTE: CSQAQ open API currently returns volume=0 for index kline on free tokens.")
        print("      Website VOL bars may require enterprise access or frontend-only metrics.")

    if not args.no_store:
        store = VolumeCrawlStore()
        saved = store.upsert_index_rows(frame.to_dict(orient="records"))
        print(f"saved_rows={saved} db={store.db_path}")

    if args.csv:
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"csv={out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
