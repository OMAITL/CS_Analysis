#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export CSQAQ daily volume data for the index and one or more items."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from market_provider.csqaq import CSQAQClient
from market_provider.csqaq.volume_export import (
    fetch_index_daily_volume_frame,
    fetch_item_daily_volume_by_query,
    fetch_item_daily_volume_frame,
)


def _safe_stem(value: str) -> str:
    normalized = re.sub(r"[\\/:*?\"<>|]+", "_", value).strip()
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = normalized.strip("._")
    return normalized or "csqaq_volume"


def _write_csv(frame: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def _build_client(args: argparse.Namespace) -> CSQAQClient:
    return CSQAQClient(
        api_token=(args.api_token or "").strip() or None,
        base_url=(args.base_url or "").strip() or None,
        timeout=float(args.timeout),
        enable_cache=not args.no_cache,
    )


def _read_item_file(path: Path) -> List[str]:
    rows: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        rows.append(item)
    return rows


def _resolve_batch_requests(args: argparse.Namespace) -> List[Tuple[str, str]]:
    requests: List[Tuple[str, str]] = []

    for query in args.item_query or []:
        cleaned = (query or "").strip()
        if cleaned:
            requests.append(("query", cleaned))

    for raw_good_id in args.good_id or []:
        requests.append(("good_id", str(int(raw_good_id))))

    for file_path in args.item_file or []:
        path = Path(file_path)
        for item in _read_item_file(path):
            requests.append(("query", item))

    deduped: List[Tuple[str, str]] = []
    seen = set()
    for request in requests:
        if request in seen:
            continue
        seen.add(request)
        deduped.append(request)
    return deduped


def _default_item_output(entry_market_hash_name: str, output_dir: Path) -> Path:
    return output_dir / f"{_safe_stem(entry_market_hash_name)}_daily_volume.csv"


def _run_index(args: argparse.Namespace) -> int:
    client = _build_client(args)
    frame = fetch_index_daily_volume_frame(
        client,
        sub_index_id=str(args.sub_index_id),
        period=args.period,
    )
    output = Path(args.output or "data/csqaq_index_daily_volume.csv")
    _write_csv(frame, output)
    print(f"指数成交量已导出: {output} | rows={len(frame)} | sub_index_id={args.sub_index_id}")
    return 0


def _run_item(args: argparse.Namespace) -> int:
    client = _build_client(args)
    if args.item_query:
        entry, frame, meta = fetch_item_daily_volume_by_query(
            client,
            args.item_query,
            prefer_market_hash_name=args.market_hash_name,
            price_platform=args.platform,
            period=args.period_days,
            style=args.style,
        )
    else:
        frame, meta = fetch_item_daily_volume_frame(
            client,
            args.good_id,
            price_platform=args.platform,
            period=args.period_days,
            style=args.style,
        )
        entry = None

    output = Path(args.output) if args.output else (
        _default_item_output(
            entry.market_hash_name if entry is not None else f"good_id_{args.good_id}",
            Path("data/csqaq_item_volumes"),
        )
    )
    _write_csv(frame, output)
    resolved_name = entry.market_hash_name if entry is not None else f"good_id={args.good_id}"
    print(
        "饰品成交量已导出: "
        f"{output} | rows={len(frame)} | item={resolved_name} | volume_source={meta.volume_source}"
    )
    return 0


def _run_batch(args: argparse.Namespace) -> int:
    client = _build_client(args)
    requests = _resolve_batch_requests(args)
    if not requests:
        raise SystemExit("batch 模式至少需要 --item-query / --good-id / --item-file 中的一种输入。")

    output_dir = Path(args.output_dir or "data/csqaq_item_volumes")
    combined_frames: List[pd.DataFrame] = []
    manifest_rows = []

    for request_type, value in requests:
        if request_type == "query":
            entry, frame, meta = fetch_item_daily_volume_by_query(
                client,
                value,
                price_platform=args.platform,
                period=args.period_days,
                style=args.style,
            )
        else:
            frame, meta = fetch_item_daily_volume_frame(
                client,
                int(value),
                price_platform=args.platform,
                period=args.period_days,
                style=args.style,
            )
            entry = None

        label = entry.market_hash_name if entry is not None else f"good_id_{value}"
        output_path = _default_item_output(label, output_dir)
        frame_to_save = frame.copy()
        frame_to_save["source_query"] = value
        _write_csv(frame_to_save, output_path)
        combined_frames.append(frame_to_save)
        manifest_rows.append(
            {
                "source_query": value,
                "good_id": int(frame.iloc[0]["good_id"]) if not frame.empty else (entry.id if entry else int(value)),
                "market_hash_name": frame.iloc[0]["market_hash_name"] if not frame.empty else label,
                "rows": len(frame),
                "volume_source": meta.volume_source,
                "platform": frame.iloc[0]["platform"] if not frame.empty else args.platform,
                "output_file": str(output_path),
            }
        )
        print(f"已导出 {label}: {output_path} | rows={len(frame)} | volume_source={meta.volume_source}")

    combined = pd.concat(combined_frames, ignore_index=True) if combined_frames else pd.DataFrame()
    manifest = pd.DataFrame(manifest_rows)
    combined_path = output_dir / "combined_daily_volume.csv"
    manifest_path = output_dir / "manifest.csv"
    _write_csv(combined, combined_path)
    _write_csv(manifest, manifest_path)
    print(f"批量导出完成: combined={combined_path} | manifest={manifest_path} | items={len(manifest_rows)}")
    return 0


def _add_common_fetch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-token", help="覆盖 .env 中的 CSQAQ_API_TOKEN")
    parser.add_argument("--base-url", help="覆盖 .env 中的 CSQAQ_BASE_URL")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP 超时秒数，默认 30")
    parser.add_argument("--no-cache", action="store_true", help="禁用本地 CSQAQ 缓存")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="导出 CSQAQ 饰品指数和单饰品的每日成交量数据",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="导出饰品指数的日成交量")
    _add_common_fetch_args(index_parser)
    index_parser.add_argument("--sub-index-id", default="1", help="指数 id，首页饰品指数默认 1")
    index_parser.add_argument(
        "--period",
        default="1day",
        choices=["1hour", "4hour", "1day", "7day"],
        help="指数 K 线周期，默认 1day",
    )
    index_parser.add_argument("--output", help="输出 CSV 路径")
    index_parser.set_defaults(func=_run_index)

    item_parser = subparsers.add_parser("item", help="导出单个饰品的日成交量")
    _add_common_fetch_args(item_parser)
    target_group = item_parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--item-query", help="饰品名称或 market_hash_name")
    target_group.add_argument("--good-id", type=int, help="已知 good_id 时可直接传入")
    item_parser.add_argument("--market-hash-name", help="歧义名称时指定精确的 market_hash_name")
    item_parser.add_argument("--platform", default="yyyp", choices=["buff", "yyyp", "steam"], help="价格/成交量平台")
    item_parser.add_argument("--period-days", type=int, default=365, help="拉取最近多少天，默认 365")
    item_parser.add_argument("--style", default="all_style", help="图表 style 参数，默认 all_style")
    item_parser.add_argument("--output", help="输出 CSV 路径")
    item_parser.set_defaults(func=_run_item)

    batch_parser = subparsers.add_parser("batch", help="批量导出多个饰品的日成交量")
    _add_common_fetch_args(batch_parser)
    batch_parser.add_argument("--item-query", action="append", help="可重复传入多个饰品名称")
    batch_parser.add_argument("--good-id", type=int, action="append", help="可重复传入多个 good_id")
    batch_parser.add_argument("--item-file", action="append", help="文本文件，每行一个饰品名称或 market_hash_name")
    batch_parser.add_argument("--platform", default="yyyp", choices=["buff", "yyyp", "steam"], help="价格/成交量平台")
    batch_parser.add_argument("--period-days", type=int, default=365, help="拉取最近多少天，默认 365")
    batch_parser.add_argument("--style", default="all_style", help="图表 style 参数，默认 all_style")
    batch_parser.add_argument("--output-dir", help="输出目录，默认 data/csqaq_item_volumes")
    batch_parser.set_defaults(func=_run_batch)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
