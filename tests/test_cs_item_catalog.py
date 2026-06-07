# -*- coding: utf-8 -*-
"""Tests for CS item catalog repository and sync service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.repositories.cs_item_catalog_repo import CSItemCatalogRepository
from src.services.cs_item_catalog_service import CSItemCatalogService
from src.storage import DatabaseManager


@pytest.fixture
def memory_repo():
    DatabaseManager.reset_instance()
    db = DatabaseManager(db_url="sqlite:///:memory:")
    repo = CSItemCatalogRepository(db)
    yield repo
    DatabaseManager.reset_instance()


def test_upsert_and_search_local(memory_repo):
    memory_repo.upsert_entries(
        [
            {
                "good_id": 769,
                "name": "法玛斯 | 机械工业 (崭新出厂)",
                "market_hash_name": "FAMAS | Mecha Industries (Factory New)",
            },
            {
                "good_id": 770,
                "name": "法玛斯 | 机械工业 (久经沙场)",
                "market_hash_name": "FAMAS | Mecha Industries (Field-Tested)",
            },
        ]
    )
    rows, total = memory_repo.search_items("机械工业", page_size=20)
    assert total == 2
    assert {row.good_id for row in rows} == {769, 770}


def test_search_local_by_good_id(memory_repo):
    memory_repo.upsert_entries(
        [{"good_id": 12345, "name": "测试饰品", "market_hash_name": "Test Item"}]
    )
    rows, total = memory_repo.search_items("12345", page_size=20)
    assert total == 1
    assert rows[0].good_id == 12345


def test_sync_full_parses_page_list(memory_repo):
    mock_client = MagicMock()
    mock_client.get_page_list.side_effect = [
        {
            "total": 2,
            "data": [
                {"id": 1, "name": "A", "market_hash_name": "A EN"},
                {"id": 2, "name": "B", "market_hash_name": "B EN"},
            ],
        },
        {"total": 2, "data": []},
    ]
    service = CSItemCatalogService(repo=memory_repo, client=mock_client)
    result = service.sync_full(max_pages=None)
    assert result["rows_upserted"] == 2
    assert memory_repo.count_items() == 2
    status = service.get_status()
    assert status["item_count"] == 2
    assert status["api_total"] == 2


def test_search_hybrid_prefers_local(memory_repo, monkeypatch):
    memory_repo.upsert_entries(
        [{"good_id": 71, "name": "AK-47 | 火蛇 (战痕累累)", "market_hash_name": "AK-47 | Fire Serpent (BS)"}]
    )
    mock_client = MagicMock()
    service = CSItemCatalogService(repo=memory_repo, client=mock_client)
    monkeypatch.setenv("CS_ITEM_CATALOG_LOCAL_SEARCH", "true")
    payload = service.search_hybrid("火蛇", page_size=20)
    assert payload["source"] == "local"
    assert payload["total"] == 1
    mock_client.search_goods.assert_not_called()


def test_search_hybrid_falls_back_to_csqaq(memory_repo, monkeypatch):
    mock_client = MagicMock()
    mock_client.search_goods.return_value = MagicMock(
        items=[MagicMock(id=99, name="Remote Item", market_hash_name="Remote EN")],
        page_index=1,
        page_size=20,
        total=1,
    )
    service = CSItemCatalogService(repo=memory_repo, client=mock_client)
    monkeypatch.setenv("CS_ITEM_CATALOG_LOCAL_SEARCH", "true")
    payload = service.search_hybrid("remote-only", page_size=20)
    assert payload["source"] == "csqaq"
    assert payload["items"][0]["good_id"] == 99
    assert memory_repo.count_items() == 1
