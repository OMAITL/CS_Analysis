# -*- coding: utf-8 -*-
"""Tests for ItemDataProvider crawl backfill."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.services.cs_item_data_provider import ItemDataBundle, ItemDataProvider


def test_needs_crawl_backfill_when_no_history():
    bundle = ItemDataBundle(good_id=123, meta={"crawl_rows": 0, "api_rows": 0})
    assert ItemDataProvider._needs_crawl_backfill(bundle) is True


def test_fetch_with_backfill_triggers_crawl():
    provider = ItemDataProvider()
    empty = ItemDataBundle(
        good_id=123,
        meta={"crawl_rows": 0, "api_rows": 0},
        item_info={"name": "M4A1-S | Flashback"},
    )
    filled = ItemDataBundle(
        good_id=123,
        price_history=[{"date": "2026-06-01", "close": 10.0}],
        volume_history=[{"date": "2026-06-01", "volume": 5.0}],
        trend={"signal_score": 50},
        meta={"crawl_rows": 30, "api_rows": 0, "crawl_backfill": True},
    )

    with patch.object(provider, "_fetch_once", side_effect=[empty, filled]) as fetch_mock:
        progress = MagicMock()
        result = provider.fetch_with_backfill(good_id=123, item="闪回 M4A1", progress_callback=progress)

    assert fetch_mock.call_count == 2
    assert fetch_mock.call_args_list[1].kwargs.get("refresh_crawl") is True
    progress.assert_called_once()
    assert result.price_history
