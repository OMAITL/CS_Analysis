#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync CSQAQ item catalog into local SQLite (DATABASE_PATH).

Examples:
  python scripts/sync_cs_item_catalog.py --mode full
  python scripts/sync_cs_item_catalog.py --mode incremental
  python scripts/sync_cs_item_catalog.py --mode full --resume
  python scripts/sync_cs_item_catalog.py --mode full --max-pages 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import setup_env

setup_env()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync CSQAQ item catalog to local database")
    parser.add_argument(
        "--mode",
        choices=("full", "incremental"),
        default="incremental",
        help="full = paginate entire catalog; incremental = tail/new pages",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume interrupted full sync from checkpoint_page",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit pages fetched (useful for smoke tests)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print catalog status and exit without syncing",
    )
    args = parser.parse_args(argv)

    from src.services.cs_item_catalog_service import CSItemCatalogService

    service = CSItemCatalogService()
    if args.status:
        print(json.dumps(service.get_status(), ensure_ascii=False, indent=2))
        return 0

    try:
        if args.mode == "full":
            result = service.sync_full(resume=args.resume, max_pages=args.max_pages)
        else:
            result = service.sync_incremental(max_pages=args.max_pages)
    except Exception as exc:
        print(f"[sync_cs_item_catalog] ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(service.get_status(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
