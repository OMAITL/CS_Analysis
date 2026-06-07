# -*- coding: utf-8 -*-
"""Tests for CS skill engine."""

from __future__ import annotations

from src.services.cs_entity_resolver import INTENT_MANIPULATION
from src.services.cs_item_data_provider import ItemDataBundle
from src.services.cs_skill_engine import CSSkillEngine, DetectManipulationSkill


def test_manipulation_skill_detects_volume_price_divergence():
    bundle = ItemDataBundle(
        trend={
            "bias_ma5": 9.0,
            "volume_ratio_5d": 0.7,
            "volume_status": "缩量",
            "rsi_status": "超买",
            "macd_status": "金叉",
        },
        item_info={"yyyp_sell_num": 12},
    )
    result = DetectManipulationSkill().run(bundle)
    assert result["score"] >= 45
    assert any("乖离" in s for s in result["signals"])


def test_skill_engine_runs_for_manipulation_intent():
    bundle = ItemDataBundle(
        trend={
            "bias_ma5": 5.0,
            "volume_ratio_5d": 1.2,
            "volume_status": "平量",
            "signal_score": 55,
            "buy_signal": "观望",
            "trend_status": "偏多",
            "risk_factors": [],
        },
        item_info={},
    )
    out = CSSkillEngine().run(INTENT_MANIPULATION, bundle)
    assert out.manipulation is not None
    assert out.trend is not None
    assert out.risk is not None
    assert "detect_manipulation" in out.active_skills
