# -*- coding: utf-8 -*-
"""Tests for CS market watchlist scan."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.services.cs_market_scan_service import (
    _suspicion_score,
    build_authorized_items,
    detect_market_intent,
    render_watchlist_markdown,
    scan_market_watchlist,
)


def test_detect_manipulation_intent():
    assert detect_market_intent("哪些饰品可能有人在做盘？") == "manipulation"


def test_suspicion_score_flags_low_listing_and_bias():
    score, reasons = _suspicion_score(
        {"bias_ma5": 9.0, "volume_ratio_5d": 0.8, "volume_status": "缩量", "rsi_status": "超买"},
        {"yyyp_sell_num": 12},
    )
    assert score >= 4
    assert any("乖离" in r for r in reasons)
    assert any("挂牌" in r for r in reasons)


def test_render_watchlist_uses_full_name_verbatim():
    md = render_watchlist_markdown(
        [
            {
                "good_id": 2876,
                "name": "弯刀（★） | 伽玛多普勒（Phase 2） (崭新出厂)",
                "reasons": ["乖离 MA5 达 9.0%"],
                "current_price": 1200.5,
            }
        ]
    )
    assert "2876" in md
    assert "弯刀（★） / 伽玛多普勒（Phase 2） (崭新出厂)" in md
    assert "AK-47" not in md


def test_authorized_items_dedupes():
    items = build_authorized_items(
        [{"good_id": 1, "name": "A", "market_hash_name": "A EN"}],
        [{"category": "探员", "examples": [{"good_id": 1, "name": "A"}, {"good_id": 2, "name": "B"}]}],
    )
    assert len(items) == 2
    assert {row["good_id"] for row in items} == {1, 2}


@patch("src.services.cs_market_scan_service._verify_item_identity")
@patch("src.services.cs_market_scan_service._analyze_candidate")
@patch("src.services.cs_market_scan_service._collect_candidate_good_ids")
def test_scan_returns_ranked_watchlist(mock_pool, mock_analyze, mock_verify):
    mock_verify.side_effect = lambda gid, **kw: {
        "name": kw.get("fallback_name") or str(gid),
        "market_hash_name": kw.get("fallback_mhn") or str(gid),
    }
    mock_pool.return_value = [
        {"good_id": 1, "name": "探员 A", "seed": "探员"},
        {"good_id": 2, "name": "探员 B", "seed": "探员"},
    ]
    mock_analyze.side_effect = [
        {
            "good_id": 1,
            "item_name": "探员 A",
            "trend": {
                "bias_ma5": 10,
                "volume_ratio_5d": 0.7,
                "volume_status": "缩量",
                "current_price": 100,
                "buy_signal": "观望",
                "signal_score": 55,
                "rsi_status": "超买",
                "macd_status": "金叉",
            },
            "snapshot": {"yyyp_sell_num": 8},
        },
        {
            "good_id": 2,
            "item_name": "探员 B",
            "trend": {
                "bias_ma5": 2,
                "volume_ratio_5d": 1.1,
                "volume_status": "平量",
                "current_price": 50,
                "buy_signal": "观望",
                "signal_score": 40,
                "rsi_status": "中性",
                "macd_status": "金叉",
            },
            "snapshot": {"yyyp_sell_num": 200},
        },
    ]

    result = scan_market_watchlist("哪些饰品可能有人在做盘？")
    assert result["intent"] == "manipulation"
    assert len(result["watchlist"]) >= 1
    assert result["watchlist"][0]["name"] == "探员 A"
    assert result["watchlist"][0]["score"] > 0
