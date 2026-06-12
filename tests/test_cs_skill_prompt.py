# -*- coding: utf-8 -*-
"""Tests for CS skill prompt loading."""

from __future__ import annotations

from src.services.cs_skill_prompt import (
    CS_ALLOWED_SKILL_IDS,
    CS_RECOMMENDED_SKILL_IDS,
    build_cs_skill_instructions,
    list_cs_skills_catalog,
    normalize_cs_skill_ids,
    resolve_cs_skill_prompt,
)


def test_normalize_defaults_to_bull_trend():
    assert normalize_cs_skill_ids(None) == ["bull_trend"]
    assert normalize_cs_skill_ids([]) == ["bull_trend"]


def test_normalize_filters_unknown():
    assert normalize_cs_skill_ids(["bull_trend", "growth_quality", "event_driven"]) == [
        "bull_trend",
        "event_driven",
    ]


def test_cs_adapted_skill_loads_from_strategies_cs():
    text = build_cs_skill_instructions(["event_driven"])
    assert "CS 事件驱动" in text
    assert "search_stock_news" not in text


def test_technical_skill_loads_from_strategies_cs():
    text = build_cs_skill_instructions(["bull_trend"])
    assert "缩量回踩" in text
    assert "放量突破" in text
    assert "get_daily_history" not in text


def test_resolve_includes_all_allowed_ids():
    state = resolve_cs_skill_prompt(["event_driven", "dragon_head"])
    assert state.active_skill_ids == ("event_driven", "dragon_head")
    assert "事件驱动" in state.skill_instructions
    assert "相对强势" in state.skill_instructions


def test_cs_native_skill_loads():
    text = build_cs_skill_instructions(["platform_arbitrage", "manipulation_radar"])
    assert "跨平台价差" in text
    assert "做盘雷达" in text
    assert "get_daily_history" not in text


def test_allowed_skill_count():
    assert len(CS_ALLOWED_SKILL_IDS) == 11


def test_skills_catalog_includes_recommended():
    catalog = list_cs_skills_catalog()
    assert len(catalog["skills"]) == 11
    assert catalog["default"] == ["bull_trend"]
    assert catalog["recommended"] == list(CS_RECOMMENDED_SKILL_IDS)
    assert "cs_native" in catalog["category_labels"]
