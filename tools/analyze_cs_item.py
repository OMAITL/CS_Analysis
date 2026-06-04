#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze one CS item: fused OHLCV -> StockTrendAnalyzer."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from crawlers.csqaq.browser_crawler import CSQAQBrowserCrawler  # noqa: E402
from crawlers.csqaq.store import VolumeCrawlStore  # noqa: E402
from market_provider.csqaq.analysis_store import CSAnalysisStore  # noqa: E402
from market_provider.csqaq.client import CSQAQClient  # noqa: E402
from market_provider.csqaq.item_ohlcv_builder import ItemOhlcvBuilder  # noqa: E402
from src.stock_analyzer import StockTrendAnalyzer  # noqa: E402

DEFAULT_ITEM = "AK-47 | Redline (Field-Tested)"


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


def _print_snapshot(client: CSQAQClient, good_id: int) -> None:
    detail = client.get_item_good(good_id)
    goods = detail.get("goods_info") or {}
    print("\n=== Item Snapshot ===")
    for key in (
        "name",
        "market_hash_name",
        "buff_sell_price",
        "yyyp_sell_price",
        "steam_sell_price",
        "buff_sell_num",
        "yyyp_sell_num",
        "turnover_number",
        "updated_at",
    ):
        if goods.get(key) is not None:
            print(f"{key}: {goods.get(key)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="CS item fused OHLCV trend analysis")
    parser.add_argument("--item", default=DEFAULT_ITEM, help="Item query or market_hash_name")
    parser.add_argument("--good-id", type=int, default=0)
    parser.add_argument("--platform", default="", help="buff | yyyp | steam")
    parser.add_argument("--period", type=int, default=365)
    parser.add_argument("--no-crawl", action="store_true", help="API-only OHLCV (skip crawler DB)")
    parser.add_argument("--refresh-crawl", action="store_true", help="Playwright K-line crawl before build")
    parser.add_argument("--kline-pages", type=int, default=5)
    parser.add_argument("--json", default="", help="Write analysis summary JSON to path")
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
    platform = args.platform.strip() or None

    if args.good_id:
        detail = client.get_item_good(args.good_id)
        goods = detail.get("goods_info") or {}
        good_id = int(args.good_id)
        code = str(goods.get("market_hash_name") or good_id)
    else:
        entry = client.resolve_good_id(args.item, prefer_market_hash_name=args.item)
        good_id = entry.id
        code = entry.market_hash_name

    if args.refresh_crawl:
        goods = client.get_item_good(good_id).get("goods_info") or {}
        browser = CSQAQBrowserCrawler()
        crawl_frame = browser.crawl_item_kline_volume(
            good_id,
            platform=platform,
            max_pages=args.kline_pages,
            item_name=str(goods.get("name") or good_id),
            market_hash_name=str(goods.get("market_hash_name") or good_id),
        )
        if not crawl_frame.empty:
            VolumeCrawlStore().upsert_item_rows(crawl_frame.to_dict(orient="records"))

    builder = ItemOhlcvBuilder(client=client)
    frame, meta = builder.build(
        good_id,
        platform=platform,
        period=args.period,
        prefer_crawl=not args.no_crawl,
    )

    print(
        f"\nOHLCV rows={meta.row_count} quality={meta.data_quality} "
        f"ohlc_source={meta.ohlc_source} volume_source={meta.volume_source} "
        f"crawl_rows={meta.crawl_rows} api_rows={meta.api_rows}"
    )
    if frame.empty:
        print("ERROR: empty OHLCV frame.")
        return 1

    print(frame[["date", "open", "high", "low", "close", "volume", "volume_source"]].tail(8).to_string(index=False))

    if not args.no_store:
        CSAnalysisStore().upsert_item_ohlcv_rows(frame.to_dict(orient="records"))

    _print_snapshot(client, good_id)

    analyzer = StockTrendAnalyzer()
    trend_input = frame[["date", "open", "high", "low", "close", "volume", "amount", "pct_chg"]].copy()
    result = analyzer.analyze(trend_input, code=code)
    _print_trend_result(result)

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "good_id": good_id,
            "market_hash_name": code,
            "meta": meta.model_dump(),
            "trend": {
                "trend_status": result.trend_status.value,
                "buy_signal": result.buy_signal.value,
                "signal_score": result.signal_score,
                "volume_status": result.volume_status.value,
                "volume_ratio_5d": result.volume_ratio_5d,
                "macd_status": result.macd_status.value,
                "rsi_status": result.rsi_status.value,
                "signal_reasons": result.signal_reasons,
                "risk_factors": result.risk_factors,
            },
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\njson={out}")

    if result.risk_factors and "数据不足" in "".join(result.risk_factors):
        print("\nWARNING: insufficient bars for full analysis (<20).")
        return 1

    print("\nOK: CS item analysis completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
