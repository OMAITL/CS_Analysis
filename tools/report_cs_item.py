#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate CS item Markdown report (LLM + template fallback)."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from market_provider.csqaq.cs_report import CSItemReportGenerator  # noqa: E402
from market_provider.csqaq.item_analysis import run_cs_item_analysis  # noqa: E402
from src.services.cs_event_intel_service import fetch_cs_event_intel  # noqa: E402

DEFAULT_ITEM = "AK-47 | Redline (Field-Tested)"


def _default_output_path(good_id: int, item_name: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in item_name)[:40]
    return Path("reports") / "cs" / f"{good_id}_{safe}_{stamp}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CS item LLM Markdown report")
    parser.add_argument("--item", default="", help="Item query or market_hash_name")
    parser.add_argument("--good-id", type=int, default=0)
    parser.add_argument("--platform", default="", help="buff | yyyp | steam")
    parser.add_argument("--period", type=int, default=365)
    parser.add_argument("--no-crawl", action="store_true", help="API-only OHLCV")
    parser.add_argument("--refresh-crawl", action="store_true")
    parser.add_argument("--kline-pages", type=int, default=5)
    parser.add_argument("-o", "--output", default="", help="Markdown output path")
    parser.add_argument("--print-only", action="store_true", help="Print report to stdout, do not write file")
    parser.add_argument(
        "--skills",
        default="",
        help="Comma-separated skill ids (default bull_trend). See strategies/cs/ and GET /api/v1/cs/items/skills",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not args.good_id and not args.item.strip():
        args.item = DEFAULT_ITEM

    platform = args.platform.strip() or None
    skills = [s.strip() for s in args.skills.split(",") if s.strip()] or None
    try:
        ctx = run_cs_item_analysis(
            good_id=args.good_id or None,
            item_query=args.item.strip() or None,
            platform=platform,
            period=args.period,
            prefer_crawl=not args.no_crawl,
            refresh_crawl=args.refresh_crawl,
            kline_pages=args.kline_pages,
        )
    except Exception as exc:
        print(f"ERROR: analysis failed: {exc}")
        return 1

    event_context, _ = fetch_cs_event_intel(
        ctx.good_id,
        ctx.item_name,
        ctx.market_hash_name,
    )
    ctx.event_context = event_context

    report, source = CSItemReportGenerator().generate(ctx, skills=skills)
    print(f"report_source={source} good_id={ctx.good_id} signal={ctx.trend.buy_signal.value}")

    if args.print_only:
        print("\n" + report)
        return 0

    out = Path(args.output) if args.output else _default_output_path(ctx.good_id, ctx.item_name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"report={out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
