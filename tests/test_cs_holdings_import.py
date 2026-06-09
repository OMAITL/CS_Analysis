# -*- coding: utf-8 -*-
"""Tests for CS holdings import pipeline (draft, dedup, match, commit)."""

from __future__ import annotations

import pytest

from src.services.cs_holdings_dedup import compute_dedup_key, normalize_wear, reconcile_item_name_and_wear
from src.services.cs_holdings_import_service import CSHoldingsImportService, _sessions, _sessions_lock
from src.services.cs_holdings_match_engine import match_holding_item
from src.storage import CSHolding, DatabaseManager


@pytest.fixture
def holdings_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cs_holdings_import.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    DatabaseManager.reset_instance()
    db = DatabaseManager.get_instance()
    yield db
    DatabaseManager.reset_instance()


def test_normalize_wear_aliases():
    assert normalize_wear("FN") == "崭新出厂"
    assert normalize_wear("略有磨损") == "略有磨损"


def test_reconcile_item_name_and_wear_prefers_suffix_in_name():
    name = "运动手套 (★) | 树篱迷宫 (略有磨损)"
    _, wear = reconcile_item_name_and_wear(name, "久经沙场")
    assert wear == "略有磨损"


def test_compute_dedup_key_stable():
    key_a = compute_dedup_key(
        item_name="AK-47 | 红线 (久经沙场)",
        wear="久经沙场",
        float_value=0.2312,
        platform="yyyp",
    )
    key_b = compute_dedup_key(
        item_name="ak-47 | 红线",
        wear="FT",
        float_value=0.23119,
        platform="yyyp",
    )
    assert key_a == key_b


def test_match_holding_item_with_explicit_good_id():
    result = match_holding_item(item_name="测试饰品", wear="", good_id=769)
    assert result.good_id == 769
    assert result.match_tier == "exact"
    assert result.match_confidence == "high"


def test_preview_and_commit_manual_import(holdings_db, monkeypatch):
    monkeypatch.setattr(
        "src.services.cs_holdings_import_service.match_holding_item",
        lambda **kwargs: __import__(
            "src.services.cs_holdings_match_engine", fromlist=["MatchResult"]
        ).MatchResult(
            good_id=769,
            item_name=kwargs.get("item_name") or "",
            match_tier="exact",
            match_confidence="high",
            match_score=1.0,
        ),
    )
    monkeypatch.setattr(
        "src.services.cs_holdings_service.CSHoldingsService._refresh_row_prices",
        lambda self, row: {
            "id": row.id,
            "good_id": row.good_id,
            "item_name": row.item_name,
            "wear": row.wear or "",
            "platform": row.platform,
            "quantity": row.quantity,
            "purchase_price": row.purchase_price,
            "market_price": row.market_price,
            "cost_total": row.purchase_price,
            "market_total": row.market_price,
            "pnl": 0,
            "pnl_pct": 0,
            "thumbnail_url": None,
            "note": row.note,
            "dedup_key": row.dedup_key,
            "import_batch_id": row.import_batch_id,
            "created_at": None,
            "updated_at": None,
        },
    )

    with _sessions_lock:
        _sessions.clear()

    service = CSHoldingsImportService()
    preview = service.preview_from_items(
        source="manual",
        items=[
            {
                "item_name": "AK-47 | 红线 (久经沙场)",
                "wear": "久经沙场",
                "purchase_price": 100,
                "platform": "yyyp",
            }
        ],
    )
    assert preview["session_id"]
    assert len(preview["drafts"]) == 1
    assert preview["drafts"][0]["good_id"] == 769

    result = service.commit_session(preview["session_id"])
    assert result["imported_count"] == 1
    assert result["batch_id"]

    with holdings_db.get_session() as session:
        from sqlalchemy import select

        rows = session.execute(select(CSHolding)).scalars().all()
        assert any(r.good_id == 769 for r in rows)
        assert rows[0].dedup_key


def test_skip_duplicates_on_commit(holdings_db, monkeypatch):
    monkeypatch.setattr(
        "src.services.cs_holdings_import_service.match_holding_item",
        lambda **kwargs: __import__(
            "src.services.cs_holdings_match_engine", fromlist=["MatchResult"]
        ).MatchResult(
            good_id=769,
            item_name=kwargs.get("item_name") or "",
            match_tier="exact",
            match_confidence="high",
            match_score=1.0,
        ),
    )
    monkeypatch.setattr(
        "src.services.cs_holdings_service.CSHoldingsService._refresh_row_prices",
        lambda self, row: {"id": row.id, "item_name": row.item_name, "quantity": 1},
    )

    with _sessions_lock:
        _sessions.clear()

    service = CSHoldingsImportService()
    first = service.preview_from_items(
        source="manual",
        items=[{"item_name": "AK-47 | 红线 (久经沙场)", "wear": "久经沙场", "purchase_price": 50}],
    )
    service.commit_session(first["session_id"])

    second = service.preview_from_items(
        source="manual",
        items=[{"item_name": "AK-47 | 红线 (久经沙场)", "wear": "久经沙场", "purchase_price": 60}],
    )
    assert second["drafts"][0]["duplicate_of"] is not None

    result = service.commit_session(second["session_id"], skip_duplicates=True)
    assert result["skipped_duplicates"] == 1
    assert result["imported_count"] == 0
