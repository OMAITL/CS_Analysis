#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build fused CS item daily OHLCV (Open API + crawler K-line) and persist."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

import pandas as pd  # noqa: E402

from crawlers.csqaq.browser_crawler import CSQAQBrowserCrawler  # noqa: E402
from crawlers.csqaq.store import VolumeCrawlStore  # noqa: E402
from market_provider.csqaq.analysis_store import CSAnalysisStore  # noqa: E402
from market_provider.csqaq.client import CSQAQClient  # noqa: E402
from market_provider.csqaq.item_ohlcv_builder import ItemOhlcvBuilder  # noqa: E402


def _parse_good_ids(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def _refresh_crawl(
    client: CSQAQClient,
    good_id: int,
    *,
    platform: str | None,
    kline_pages: int,
) -> None:
    detail = client.get_item_good(good_id)
    goods = detail.get("goods_info") or {}
    item_name = str(goods.get("name") or good_id)
    market_hash_name = str(goods.get("market_hash_name") or good_id)
    browser = CSQAQBrowserCrawler()
    frame = browser.crawl_item_kline_volume(
        good_id,
        platform=platform,
        max_pages=kline_pages,
        item_name=item_name,
        market_hash_name=market_hash_name,
    )
    if frame.empty:
        logging.warning("good_id=%s refresh crawl returned no rows", good_id)
        return
    saved = VolumeCrawlStore().upsert_item_rows(frame.to_dict(orient="records"))
    logging.info("good_id=%s refresh crawl saved_rows=%s", good_id, saved)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build fused CS item OHLCV (API + crawler)")
    parser.add_argument("--good-ids", default="", help="Comma-separated good_id list")
    parser.add_argument("--item", default="", help="Item query when --good-ids omitted")
    parser.add_argument("--platform", default="", help="buff | yyyp | steam")
    parser.add_argument("--period", type=int, default=365)
    parser.add_argument("--no-crawl", action="store_true", help="Skip reading crawler DB (API only)")
    parser.add_argument("--refresh-crawl", action="store_true", help="Run Playwright K-line crawl first")
    parser.add_argument("--kline-pages", type=int, default=5)
    parser.add_argument("--csv", default="", help="Optional CSV export path")
    parser.add_argument("--no-store", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    client = CSQAQClient()
    builder = ItemOhlcvBuilder(client=client)
    platform = args.platform.strip() or None
    prefer_crawl = not args.no_crawl

    targets: list[int] = []
    if args.good_ids.strip():
        targets = _parse_good_ids(args.good_ids)
    elif args.item.strip():
        entry = client.resolve_good_id(args.item, prefer_market_hash_name=args.item)
        targets = [entry.id]
    else:
        print("Provide --good-ids or --item")
        return 2

    frames: list[pd.DataFrame] = []
    for good_id in targets:
        if args.refresh_crawl:
            _refresh_crawl(client, good_id, platform=platform, kline_pages=args.kline_pages)
        frame, meta = builder.build(
            good_id,
            platform=platform,
            period=args.period,
            prefer_crawl=prefer_crawl,
        )
        if frame.empty:
            logging.warning("good_id=%s produced empty OHLCV", good_id)
            continue
        print(
            f"good_id={good_id} rows={meta.row_count} quality={meta.data_quality} "
            f"ohlc={meta.ohlc_source} volume={meta.volume_source} crawl_rows={meta.crawl_rows}"
        )
        print(frame[["date", "open", "high", "low", "close", "volume"]].tail(5).to_string(index=False))
        frames.append(frame)

    if not frames:
        print("No OHLCV rows built.")
        return 1

    combined = pd.concat(frames, ignore_index=True)
    if not args.no_store:
        store = CSAnalysisStore()
        saved = store.upsert_item_ohlcv_rows(combined.to_dict(orient="records"))
        print(f"saved_rows={saved} db={store.db_path}")

    if args.csv:
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"csv={out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
