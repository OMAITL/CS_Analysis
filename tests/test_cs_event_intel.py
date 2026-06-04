# -*- coding: utf-8 -*-
"""Tests for CS event intel search helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.search_service import SearchResponse, SearchResult, SearchService


def _mock_response(query: str, title: str) -> SearchResponse:
    return SearchResponse(
        query=query,
        results=[
            SearchResult(
                title=title,
                snippet="snippet",
                url="https://example.com/a",
                source="example.com",
            )
        ],
        provider="Mock",
        success=True,
    )


def test_search_cs_event_intel_builds_dimensions():
    service = SearchService()
    service._providers = [MagicMock(is_available=True, name="Mock")]

    def fake_search(query, max_results, days, topic=None):
        return _mock_response(query, f"hit:{query[:20]}")

    service._providers[0].search = fake_search

    results = service.search_cs_event_intel(
        769,
        "法玛斯 | 机械工业 (崭新出厂)",
        "FAMAS | Mecha Industries (Factory New)",
        max_searches=9,
        search_days=7,
        case_labels=["手套武器箱"],
    )
    assert "official_update" in results
    assert "case_focus" in results
    assert "tieba" in results
    assert results["official_update"].success


def test_filter_cs_event_drops_off_topic_tieba():
    service = SearchService()
    raw = SearchResponse(
        query="q",
        results=[
            SearchResult(
                title="金属探测器吧",
                snippet="探测器",
                url="https://tieba.baidu.com/f?kw=金属探测器",
                source="tieba.baidu.com",
            ),
            SearchResult(
                title="CS2 法玛斯 饰品 价格讨论",
                snippet="CS2 饰品市场",
                url="https://tieba.baidu.com/f?kw=cs2",
                source="tieba.baidu.com",
            ),
        ],
        provider="Mock",
        success=True,
    )
    filtered = service._filter_cs_event_relevance(
        raw,
        dimension="tieba",
        item_name="法玛斯 | 机械工业",
        weapon="FAMAS",
        max_results=3,
    )
    assert len(filtered.results) == 1
    assert "CS2" in filtered.results[0].title or "法玛斯" in filtered.results[0].title


def test_filter_cs_event_requires_hltv_domain():
    service = SearchService()
    raw = SearchResponse(
        query="q",
        results=[
            SearchResult(
                title="Fox Sports NHL",
                snippet="Stanley Cup",
                url="https://www.foxsports.com/article",
                source="foxsports.com",
            ),
            SearchResult(
                title="CS2 patch notes",
                snippet="Counter-Strike 2",
                url="https://www.hltv.org/news/123",
                source="hltv.org",
            ),
        ],
        provider="Mock",
        success=True,
    )
    filtered = service._filter_cs_event_relevance(
        raw,
        dimension="hltv",
        item_name="test",
        weapon="",
        max_results=3,
    )
    assert len(filtered.results) == 1
    assert "hltv.org" in filtered.results[0].url


def test_format_cs_event_report_includes_labels():
    service = SearchService()
    intel = {
        "major_sticker": _mock_response("q", "Major sticker news"),
    }
    text = service.format_cs_event_report(intel, "Test Item")
    assert "Major/贴纸" in text
    assert "Major sticker news" in text


@patch("src.services.cs_event_intel_service.get_search_service")
@patch("src.services.cs_event_intel_service.get_config")
def test_fetch_cs_event_intel_disabled(mock_cfg, mock_get_service):
    from src.services.cs_event_intel_service import fetch_cs_event_intel

    mock_cfg.return_value = MagicMock(
        cs_event_intel_enabled=False,
        news_max_age_days=7,
        cs_news_strategy_profile="medium",
        cs_event_intel_max_searches=5,
    )
    text, items = fetch_cs_event_intel(1, "item", "hash")
    assert text == ""
    assert items == []
    mock_get_service.assert_not_called()
