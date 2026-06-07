# -*- coding: utf-8 -*-
"""Tests for CS item good_id search API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from market_provider.csqaq.schemas import GoodIdEntry, GoodIdSearchResult
from src.services.cs_item_service import CSItemService


@patch("src.services.cs_item_catalog_service.CSItemCatalogService")
def test_search_items_maps_csqaq_payload(mock_catalog_cls):
    mock_catalog = MagicMock()
    mock_catalog_cls.return_value = mock_catalog
    mock_catalog.search_hybrid.return_value = {
        "items": [
            {"good_id": 769, "name": "法玛斯 | 机械工业 (崭新出厂)", "market_hash_name": "FAMAS | Mecha Industries (Factory New)"},
            {"good_id": 770, "name": "法玛斯 | 机械工业 (久经沙场)", "market_hash_name": "FAMAS | Mecha Industries (Field-Tested)"},
        ],
        "page_index": 1,
        "page_size": 20,
        "total": 5,
        "source": "local",
    }

    payload = CSItemService().search_items("机械工业", page_size=20)

    assert payload["total"] == 5
    assert len(payload["items"]) == 2
    assert payload["items"][0]["good_id"] == 769
    assert "source" not in payload
    mock_catalog.search_hybrid.assert_called_once_with("机械工业", page_index=1, page_size=20)


@patch("market_provider.csqaq.client.CSQAQClient")
def test_search_items_remote_calls_csqaq(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.search_goods.return_value = GoodIdSearchResult(
        items=[
            GoodIdEntry(id=769, name="法玛斯 | 机械工业 (崭新出厂)", market_hash_name="FAMAS | Mecha Industries (Factory New)"),
        ],
        page_index=1,
        page_size=20,
        total=1,
    )

    payload = CSItemService().search_items_remote("机械工业", page_size=20)

    assert payload["total"] == 1
    assert payload["items"][0]["good_id"] == 769
    mock_client.search_goods.assert_called_once_with("机械工业", page_index=1, page_size=20)


def test_search_items_requires_term():
    try:
        CSItemService().search_items("  ")
    except ValueError as exc:
        assert "search" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")
