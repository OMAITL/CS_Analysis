# -*- coding: utf-8 -*-
"""Tests for CS item resolve service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.services.cs_item_resolve_service import (
    expand_item_search_queries,
    resolve_good_id_from_queries,
    score_item_match,
)


def test_expand_compact_skin_weapon_without_space():
    variants = expand_item_search_queries("闪回M4A1")
    assert "M4A1 闪回" in variants
    assert "M4A1-S | 闪回" in variants


def test_expand_compact_weapon_skin_without_space():
    variants = expand_item_search_queries("M4A1闪回")
    assert "M4A1 闪回" in variants
    assert "M4A1 | 闪回" in variants
    assert "M4A1-S | 闪回" in variants


def test_expand_skin_weapon_query():
    variants = expand_item_search_queries("闪回 M4A1")
    assert "闪回 M4A1" in variants
    assert any("M4A1" in v and "闪回" in v for v in variants)


def test_score_item_match_compact_name():
    score = score_item_match(
        "法玛斯机械工业",
        "法玛斯 | 机械工业 (崭新出厂)",
        "FAMAS | Mecha Industries (Factory New)",
    )
    assert score >= 0.85


def test_expand_glove_pipe_item_name():
    variants = expand_item_search_queries("★ 运动手套 | 树篱迷宫 (久经沙场)")
    assert "运动手套 | 树篱迷宫" in variants
    assert "★ 运动手套 | 树篱迷宫" in variants
    assert "树篱迷宫" in variants


def test_expand_moto_glove_name():
    variants = expand_item_search_queries("★ 摩托手套 | 薄荷 (略有磨损)")
    assert any("摩托手套" in v and "薄荷" in v for v in variants)


def test_score_glove_name_with_star():
    score = score_item_match(
        "★ 专业手套 | 渐变大理石 (久经沙场)",
        "专业手套（★） | 渐变大理石 (久经沙场)",
        "★ Specialist Gloves | Fade (Field-Tested)",
    )
    assert score >= 0.85


@patch("src.services.cs_item_resolve_service.lookup_item_in_catalog")
@patch("src.services.cs_item_catalog_service.CSItemCatalogService")
def test_hybrid_fallback_when_catalog_misses(mock_service_cls, mock_catalog_lookup):
    mock_catalog_lookup.return_value = (None, "", "", 0.0, [])
    mock_service_cls.return_value.search_hybrid.return_value = {
        "items": [
            {
                "good_id": 1234,
                "name": "M4A1 消音型 | 闪回 (崭新出厂)",
                "market_hash_name": "M4A1-S | Flashback (Factory New)",
            }
        ],
        "source": "csqaq",
        "total": 1,
    }

    gid, name, _mhn, score, _query, _candidates = resolve_good_id_from_queries(["闪回 M4A1"])
    assert gid == 1234
    assert score >= 0.3
    assert "闪回" in name or "Flashback" in name
