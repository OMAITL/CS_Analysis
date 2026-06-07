# -*- coding: utf-8 -*-
"""Tests for rematching missing CS holdings good_id."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.repositories.cs_holdings_repo import CSHoldingsRepository
from src.services.cs_holdings_service import CSHoldingsService
from src.storage import CSHolding, DatabaseManager


@pytest.fixture
def holdings_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cs_holdings_rematch.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    DatabaseManager.reset_instance()
    db = DatabaseManager.get_instance()
    yield db
    DatabaseManager.reset_instance()


def test_rematch_missing_good_ids_updates_row(holdings_db):
    repo = CSHoldingsRepository()
    row = repo.create(
        {
            "item_name": "★ 运动手套 | 树篱迷宫 (久经沙场)",
            "wear": "久经沙场",
            "platform": "yyyp",
            "quantity": 1,
            "purchase_price": 100.0,
        }
    )
    assert row.good_id is None

    fake_match = __import__(
        "src.services.cs_holdings_match_engine", fromlist=["MatchResult"]
    ).MatchResult(
        good_id=8888,
        item_name="运动手套（★） | 树篱迷宫 (久经沙场)",
        market_hash_name="★ Sport Gloves | Hedge Maze (Field-Tested)",
        match_tier="remote",
        match_confidence="high",
        match_score=0.9,
    )

    with patch("src.services.cs_holdings_service.match_holding_item", return_value=fake_match), patch.object(
        CSHoldingsService,
        "_refresh_row_prices",
        lambda self, r: {"id": r.id, "good_id": r.good_id, "item_name": r.item_name},
    ):
        summary = CSHoldingsService(repo=repo).rematch_missing_good_ids()

    assert summary["attempted"] == 1
    assert summary["matched"] == 1
    updated = repo.get(row.id)
    assert updated is not None
    assert updated.good_id == 8888
