# -*- coding: utf-8 -*-
"""Tests for CS item event intel keyword relevance."""

from __future__ import annotations

from unittest.mock import patch

from src.services.cs_item_intel_keywords import (
    build_case_search_query,
    build_cs_item_intel_keywords,
    resolve_item_containers,
    score_event_relevance,
)


def _keywords(container_names=None):
    return build_cs_item_intel_keywords(
        item_name="法玛斯 | 机械工业 (崭新出厂)",
        market_hash_name="FAMAS | Mecha Industries (Factory New)",
        good_id=769,
        container_names=container_names,
    )


def test_direct_match_famas():
    kw = _keywords()
    assert (
        score_event_relevance(
            title="FAMAS Mecha Industries price spike",
            snippet="CS2 skin market",
            dimension="item_focus",
            keywords=kw,
        )
        == "direct"
    )


def test_case_match_glove_case():
    kw = _keywords(["手套武器箱"])
    assert (
        score_event_relevance(
            title="Glove Case price rises on CS2 market",
            snippet="weapon case drop pool",
            dimension="case_focus",
            keywords=kw,
        )
        == "case"
    )


def test_build_case_search_query_includes_aliases():
    query = build_case_search_query(["手套武器箱"])
    assert "手套武器箱" in query
    assert "glove case" in query.lower()


def test_hltv_team_news_dropped():
    kw = _keywords()
    assert (
        score_event_relevance(
            title="heavygod signs multi year extension with g2",
            snippet="roster move",
            dimension="hltv_crawl",
            keywords=kw,
        )
        == "drop"
    )


def test_hltv_major_kept_as_market():
    kw = _keywords()
    assert (
        score_event_relevance(
            title="IEM Cologne Major stage 1 recap",
            snippet="Counter-Strike 2 tournament",
            dimension="hltv_crawl",
            keywords=kw,
        )
        == "market"
    )


def test_official_update_market():
    kw = _keywords()
    assert (
        score_event_relevance(
            title="Counter-Strike 2 update",
            snippet="Valve patch notes",
            dimension="official_crawl",
            keywords=kw,
        )
        == "market"
    )


def test_resolve_item_containers_from_csqaq():
    detail = {
        "container": [
            {"id": 5, "name": "手套武器箱", "price": 103.8},
        ]
    }
    with patch("market_provider.csqaq.client.CSQAQClient") as mock_cls:
        mock_cls.return_value.get_item_good.return_value = detail
        assert resolve_item_containers(769) == ["手套武器箱"]
