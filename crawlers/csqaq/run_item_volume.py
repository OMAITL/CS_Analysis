#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""Crawl CSQAQ item daily volume for catalog items or explicit good_ids."""



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

from market_provider.csqaq.client import CSQAQClient  # noqa: E402





def _parse_good_ids(raw: str) -> list[int]:

    return [int(part.strip()) for part in raw.split(",") if part.strip()]





def _item_metadata(client: CSQAQClient, good_id: int) -> tuple[str, str]:

    try:

        detail = client.get_item_good(good_id)

        goods = detail.get("goods_info") or {}

        return str(goods.get("name") or good_id), str(goods.get("market_hash_name") or good_id)

    except Exception:

        return str(good_id), str(good_id)





def main() -> int:

    parser = argparse.ArgumentParser(description="Crawl CSQAQ item daily volume")

    parser.add_argument("--good-ids", default="", help="Comma-separated good_id list, e.g. 135,769")

    parser.add_argument("--max-pages", type=int, default=3, help="Catalog pages when --good-ids omitted")

    parser.add_argument("--page-size", type=int, default=100)

    parser.add_argument("--period", type=int, default=365, help="Chart lookback days (API fallback only)")

    parser.add_argument("--platform", default="", help="buff | yyyp | steam (default from CSQAQ_PRICE_PLATFORM)")

    parser.add_argument("--kline-pages", type=int, default=5, help="chartAll pagination depth (150 bars/page)")

    parser.add_argument("--csv", default="", help="Optional CSV export path")

    parser.add_argument(

        "--browser-kline",

        action="store_true",

        help="Crawl K-line chart volume (成交量) via Playwright chartAll – matches website tooltip",

    )

    parser.add_argument(

        "--browser",

        action="store_true",

        help="Deprecated alias for --browser-kline",

    )

    parser.add_argument("--no-store", action="store_true")

    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()



    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")

    if hasattr(sys.stdout, "reconfigure"):

        try:

            sys.stdout.reconfigure(encoding="utf-8")

        except Exception:

            pass



    use_browser_kline = args.browser_kline or args.browser

    crawler = CSQAQVolumeCrawler()

    platform = args.platform.strip() or None



    if args.good_ids.strip():

        frames = []

        client = CSQAQClient()

        for good_id in _parse_good_ids(args.good_ids):

            if use_browser_kline:

                item_name, market_hash_name = _item_metadata(client, good_id)

                browser = CSQAQBrowserCrawler()

                part = browser.crawl_item_kline_volume(

                    good_id,

                    platform=platform,

                    max_pages=args.kline_pages,

                    item_name=item_name,

                    market_hash_name=market_hash_name,

                )

            else:

                part = crawler.crawl_item_volume(good_id, platform=platform, period=args.period)

            if not part.empty:

                frames.append(part)

        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    else:

        if use_browser_kline:

            print("--browser-kline requires --good-ids (catalog crawl uses Open API fallback).")

            return 2

        frame = crawler.crawl_items_from_catalog(

            page_size=args.page_size,

            max_pages=args.max_pages,

            platform=platform,

            period=args.period,

        )



    if frame.empty:

        print("No item volume rows captured.")

        if use_browser_kline:

            print("Hint: pip install playwright && python -m playwright install chromium")

        return 1



    display_cols = [

        c for c in ["good_id", "item_name", "date", "volume", "close", "volume_source", "platform"] if c in frame.columns

    ]

    print(frame[display_cols].tail(15).to_string(index=False))

    print(f"\nrows={len(frame)} sources={frame['volume_source'].value_counts().to_dict()}")



    if not args.no_store:

        item_rows = frame[frame["date"].notna() & frame["volume"].notna()].copy()

        store = VolumeCrawlStore()

        saved = store.upsert_item_rows(item_rows.to_dict(orient="records"))

        print(f"saved_rows={saved} db={store.db_path}")



    if args.csv:

        out = Path(args.csv)

        out.parent.mkdir(parents=True, exist_ok=True)

        frame.to_csv(out, index=False, encoding="utf-8-sig")

        print(f"csv={out}")



    return 0





if __name__ == "__main__":

    raise SystemExit(main())

