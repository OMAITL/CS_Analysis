# -*- coding: utf-8 -*-
"""Code-first skill engine for CS chat (no LLM analysis)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.services.cs_entity_resolver import (
    INTENT_BUY_SELL,
    INTENT_EXPLAIN,
    INTENT_GENERAL,
    INTENT_MANIPULATION,
    INTENT_RISK,
    INTENT_TREND,
)
from src.services.cs_item_data_provider import ItemDataBundle


@dataclass
class SkillEngineResult:
    manipulation: Optional[Dict[str, Any]] = None
    trend: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    active_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manipulation": self.manipulation,
            "trend": self.trend,
            "risk": self.risk,
            "active_skills": self.active_skills,
        }


def _clamp_score(value: float, *, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, round(value, 1)))


class DetectManipulationSkill:
    """Rule-based manipulation suspicion scoring."""

    def run(self, bundle: ItemDataBundle) -> Dict[str, Any]:
        trend = bundle.trend or {}
        snapshot = bundle.item_info or {}
        raw_score, reasons = self._score(trend, snapshot)
        score = _clamp_score(raw_score * 10)
        probability = "高" if score >= 70 else "中" if score >= 45 else "低"
        return {
            "score": score,
            "probability": probability,
            "signals": reasons,
            "summary": self._summary(score, reasons),
        }

    @staticmethod
    def _score(trend: Dict[str, Any], snapshot: Dict[str, Any]) -> tuple[float, List[str]]:
        score = 0.0
        reasons: List[str] = []

        bias = float(trend.get("bias_ma5") or 0)
        vr = float(trend.get("volume_ratio_5d") or 0)
        vol_status = str(trend.get("volume_status") or "")
        rsi_status = str(trend.get("rsi_status") or "")
        macd_status = str(trend.get("macd_status") or "")

        yyyp_num = snapshot.get("yyyp_sell_num")
        buff_num = snapshot.get("buff_sell_num")
        listing = None
        for raw in (yyyp_num, buff_num):
            if raw is None:
                continue
            try:
                listing = int(raw)
                break
            except (TypeError, ValueError):
                continue

        if bias >= 8:
            score += 2.5
            reasons.append(f"乖离 MA5 达 {bias:.1f}%")
        elif bias >= 5:
            score += 1.5
            reasons.append(f"乖离 MA5 {bias:.1f}%")

        if vol_status == "缩量" and bias >= 4:
            score += 2.0
            reasons.append("价升量缩（筹码锁定嫌疑）")

        if vr >= 3 and bias < 2:
            score += 2.0
            reasons.append(f"量比 {vr:.1f} 但涨幅有限（对倒/做量嫌疑）")
        elif vr >= 2 and bias >= 3:
            score += 1.0
            reasons.append(f"成交量放大 {vr:.1f} 倍")

        if "超买" in rsi_status or "偏高" in rsi_status:
            score += 1.0
            reasons.append(f"RSI 状态：{rsi_status}")

        if macd_status == "死叉" and bias >= 5:
            score += 1.5
            reasons.append("高位 MACD 死叉")

        if listing is not None and listing <= 25:
            score += 1.5
            reasons.append(f"挂牌量偏低（{listing}）")

        if not reasons:
            reasons.append("未发现明显做盘特征")
        return score, reasons

    @staticmethod
    def _summary(score: float, reasons: List[str]) -> str:
        if score >= 70:
            return "多项量价/挂牌信号叠加，做盘嫌疑较高"
        if score >= 45:
            return "存在部分可疑信号，需结合品类与事件进一步确认"
        return "当前数据未显示明显做盘特征"


class TrendSkill:
    """Structured trend readout from pre-computed analyzer output."""

    def run(self, bundle: ItemDataBundle) -> Dict[str, Any]:
        trend = bundle.trend or {}
        signal_score = int(trend.get("signal_score") or 0)
        return {
            "score": signal_score,
            "trend_status": trend.get("trend_status") or "",
            "ma_alignment": trend.get("ma_alignment") or "",
            "buy_signal": trend.get("buy_signal") or "",
            "current_price": trend.get("current_price"),
            "bias_ma5": trend.get("bias_ma5"),
            "volume_status": trend.get("volume_status") or "",
            "volume_ratio_5d": trend.get("volume_ratio_5d"),
            "macd_status": trend.get("macd_status") or "",
            "rsi_status": trend.get("rsi_status") or "",
            "rsi": trend.get("rsi_12"),
            "signal_reasons": list(trend.get("signal_reasons") or [])[:6],
            "summary": self._summary(trend),
        }

    @staticmethod
    def _summary(trend: Dict[str, Any]) -> str:
        parts = [
            str(trend.get("trend_status") or "").strip(),
            str(trend.get("buy_signal") or "").strip(),
        ]
        text = "，".join(p for p in parts if p)
        return text or "趋势中性"


class RiskSkill:
    """Risk level from trend risk factors + overbought signals."""

    def run(self, bundle: ItemDataBundle) -> Dict[str, Any]:
        trend = bundle.trend or {}
        meta = bundle.meta or {}
        bias = float(trend.get("bias_ma5") or 0)
        signal_score = int(trend.get("signal_score") or 0)
        rsi_status = str(trend.get("rsi_status") or "")
        risk_factors = list(trend.get("risk_factors") or [])

        score = 30.0
        signals: List[str] = list(risk_factors[:4])

        if bias >= 10:
            score += 25
            signals.append(f"乖离过大 {bias:.1f}%")
        elif bias >= 6:
            score += 15
            signals.append(f"乖离偏高 {bias:.1f}%")

        if "超买" in rsi_status:
            score += 20
            signals.append("RSI 超买")

        if str(meta.get("data_quality") or "") in {"degraded", "price_only"}:
            score += 10
            signals.append("数据质量降级")

        if signal_score <= 40:
            score += 10

        score = _clamp_score(score)
        level = "高" if score >= 70 else "中" if score >= 45 else "低"
        return {
            "score": score,
            "risk_level": level,
            "signals": signals[:6] or ["暂无明显风险信号"],
            "summary": f"综合风险等级：{level}",
        }


class CSSkillEngine:
    """Run code skills based on detected intent."""

    def __init__(self) -> None:
        self._manipulation = DetectManipulationSkill()
        self._trend = TrendSkill()
        self._risk = RiskSkill()

    def run(self, intent: str, bundle: ItemDataBundle) -> SkillEngineResult:
        if bundle.error and not bundle.trend:
            return SkillEngineResult(active_skills=[])

        result = SkillEngineResult()
        active: List[str] = []

        run_manipulation = intent in {INTENT_MANIPULATION, INTENT_EXPLAIN, INTENT_GENERAL}
        run_risk = intent in {
            INTENT_RISK,
            INTENT_BUY_SELL,
            INTENT_MANIPULATION,
            INTENT_EXPLAIN,
            INTENT_GENERAL,
        }

        if run_manipulation:
            result.manipulation = self._manipulation.run(bundle)
            active.append("detect_manipulation")

        result.trend = self._trend.run(bundle)
        active.append("trend")

        if run_risk or intent == INTENT_TREND:
            result.risk = self._risk.run(bundle)
            active.append("risk")

        result.active_skills = active
        return result
