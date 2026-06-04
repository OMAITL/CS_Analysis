#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 smoke test: fused CS item OHLCV (API + crawler) -> StockTrendAnalyzer.

Usage:
    python tools/test_cs_pipeline.py
    python tools/test_cs_pipeline.py --item "法玛斯 | 机械工业 (崭新出厂)" --refresh-crawl
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from crawlers.csqaq.browser_crawler import CSQAQBrowserCrawler  # noqa: E402
from crawlers.csqaq.store import VolumeCrawlStore  # noqa: E402
from market_provider.csqaq import (  # noqa: E402
    CSQAQAPIError,
    CSQAQClient,
    ItemOhlcvBuilder,
    index_kline_to_ohlcv,
    resolve_price_platform,
)
from src.stock_analyzer import StockTrendAnalyzer  # noqa: E402

DEFAULT_ITEM = "AK-47 | Redline (Field-Tested)"


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _print_trend_result(result) -> None:
    print("\n=== TrendAnalysisResult ===")
    print(f"code:              {result.code}")
    print(f"current_price:     {result.current_price}")
    print(f"trend_status:      {result.trend_status.value}")
    print(f"ma_alignment:      {result.ma_alignment}")
    print(f"MA5/10/20/60:      {result.ma5:.2f} / {result.ma10:.2f} / {result.ma20:.2f} / {result.ma60:.2f}")
    print(f"bias_ma5:          {result.bias_ma5:.2f}%")
    print(f"volume_status:     {result.volume_status.value}")
    print(f"volume_ratio_5d:   {result.volume_ratio_5d:.2f}")
    print(f"MACD dif/dea/bar:  {result.macd_dif:.4f} / {result.macd_dea:.4f} / {result.macd_bar:.4f}")
    print(f"macd_status:       {result.macd_status.value}")
    print(f"RSI 6/12/24:       {result.rsi_6:.2f} / {result.rsi_12:.2f} / {result.rsi_24:.2f}")
    print(f"rsi_status:        {result.rsi_status.value}")
    print(f"buy_signal:        {result.buy_signal.value}")
    print(f"signal_score:      {result.signal_score}")
    if result.signal_reasons:
        print(f"signal_reasons:    {'; '.join(result.signal_reasons)}")
    if result.risk_factors:
        print(f"risk_factors:      {'; '.join(result.risk_factors)}")


def run_item_pipeline(
    client: CSQAQClient,
    item_query: str,
    period: int,
    *,
    prefer_crawl: bool,
    refresh_crawl: bool,
    kline_pages: int,
) -> int:
    print(f"Resolving item: {item_query}")
    entry = client.resolve_good_id(item_query, prefer_market_hash_name=item_query)
    print(f"Matched good_id={entry.id} name={entry.name}")
    print(f"market_hash_name={entry.market_hash_name}")

    platform = resolve_price_platform()
    print(f"primary_platform={platform.name} (悠悠有品为默认主决策平台)")

    if refresh_crawl:
        browser = CSQAQBrowserCrawler()
        crawl_frame = browser.crawl_item_kline_volume(
            entry.id,
            platform=platform,
            max_pages=kline_pages,
            item_name=entry.name,
            market_hash_name=entry.market_hash_name,
        )
        if not crawl_frame.empty:
            VolumeCrawlStore().upsert_item_rows(crawl_frame.to_dict(orient="records"))
            print(f"refresh-crawl saved_rows={len(crawl_frame)}")

    builder = ItemOhlcvBuilder(client=client)
    df, meta = builder.build(
        entry.id,
        entry=entry,
        platform=platform,
        period=period,
        prefer_crawl=prefer_crawl,
    )
    print(
        f"\nOHLCV rows: {len(df)} | quality={meta.data_quality} | "
        f"ohlc={meta.ohlc_source} | volume={meta.volume_source} | "
        f"crawl_rows={meta.crawl_rows} | platform={meta.platform.name}"
    )
    if df.empty:
        print("ERROR: empty OHLCV frame; cannot analyze.")
        return 1
    print(df[["date", "open", "high", "low", "close", "volume"]].tail(5).to_string(index=False))

    analyzer = StockTrendAnalyzer()
    trend_input = df[["date", "open", "high", "low", "close", "volume", "amount", "pct_chg"]]
    result = analyzer.analyze(trend_input, code=entry.market_hash_name)
    _print_trend_result(result)
    if result.risk_factors and "数据不足" in "".join(result.risk_factors):
        print("\nWARNING: analyzer reported insufficient data (<20 bars).")
        return 1
    print("\nOK: CS item pipeline completed.")
    return 0


def run_index_pipeline(client: CSQAQClient, index_id: str) -> int:
    print(f"Fetching index kline id={index_id}")
    bars = client.get_index_kline(sub_index_id=index_id, period="1day")
    df = index_kline_to_ohlcv(bars)
    print(f"Index OHLCV rows: {len(df)}")
    if df.empty:
        print("ERROR: empty index OHLCV frame.")
        return 1
    print(df.tail(5).to_string(index=False))

    analyzer = StockTrendAnalyzer()
    result = analyzer.analyze(df, code=f"CS_INDEX_{index_id}")
    _print_trend_result(result)
    print("\nOK: index pipeline completed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CSQAQ fused OHLCV -> StockTrendAnalyzer smoke test")
    parser.add_argument("--item", default=DEFAULT_ITEM, help="Item query or exact market_hash_name")
    parser.add_argument("--period", type=int, default=365, help="Chart lookback days for API fallback")
    parser.add_argument("--index-id", default="", help="Optional sub-index id to test native K-line path")
    parser.add_argument("--no-crawl", action="store_true", help="API-only OHLCV")
    parser.add_argument("--refresh-crawl", action="store_true", help="Playwright K-line crawl before build")
    parser.add_argument("--kline-pages", type=int, default=5)
    parser.add_argument("--no-cache", action="store_true", help="Disable SQLite response cache")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    _configure_logging(args.verbose)

    if not os.getenv("CSQAQ_API_TOKEN", "").strip():
        print("ERROR: CSQAQ_API_TOKEN is missing.")
        print("Add it to the project root .env (see .env.example CSQAQ section) or export it in your shell.")
        return 2

    client = CSQAQClient(enable_cache=not args.no_cache)
    try:
        exit_code = run_item_pipeline(
            client,
            args.item,
            args.period,
            prefer_crawl=not args.no_crawl,
            refresh_crawl=args.refresh_crawl,
            kline_pages=args.kline_pages,
        )
        if args.index_id:
            index_code = run_index_pipeline(client, args.index_id)
            exit_code = max(exit_code, index_code)
        return exit_code
    except CSQAQAPIError as exc:
        print(f"CSQAQ API error ({exc.code}): {exc}")
        return 3
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc}")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
