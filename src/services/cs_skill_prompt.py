# -*- coding: utf-8 -*-
"""Load stock trading skills for CS item LLM reports (prompt injection only)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from src.agent.skills.base import Skill, load_skill_from_yaml

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]
_CS_SKILLS_DIR = _ROOT / "strategies" / "cs"
_BUILTIN_SKILLS_DIR = _ROOT / "strategies"

# Pure technical skills reuse stock YAML; event/structure skills use strategies/cs/ overrides.
CS_TECHNICAL_SKILL_IDS = frozenset(
    {
        "bull_trend",
        "shrink_pullback",
        "volume_breakout",
        "ma_golden_cross",
        "bottom_volume",
        "box_oscillation",
        "one_yang_three_yin",
    }
)

CS_ADAPTED_SKILL_IDS = frozenset(
    {
        "chan_theory",
        "wave_theory",
        "emotion_cycle",
        "dragon_head",
        "event_driven",
        "hot_theme",
    }
)

CS_ALLOWED_SKILL_IDS = CS_TECHNICAL_SKILL_IDS | CS_ADAPTED_SKILL_IDS

CS_DEFAULT_SKILL_IDS: tuple[str, ...] = ("bull_trend",)

CS_SKILL_DATA_MAPPING = """## CS 技能与输入数据映射（必须遵守）
- 以下技能原文可能提到股票工具名；**禁止调用任何工具**，直接使用本 prompt 下方 JSON  payload。
- `trend` 字段 ≈ `analyze_trend` 输出（MA、MACD、RSI、信号、支撑阻力等）。
- `recent_daily_bars` ≈ `get_daily_history` 最近若干日 OHLCV。
- `snapshot` 中各平台价格 ≈ 现价/挂牌参考；`volume` 为 K 线真实成交笔数，`sell_num` 仅为挂牌量。
- `event_intel` / 事件情报正文 ≈ 新闻/事件检索结果（CS 无公司公告/财报）。
- `index_summary`（若有）≈ 饰品指数近期走势，用于相对强弱判断。
- 忽略技能中关于：筹码分布、换手率、涨停、板块排名、PE/财报、减持/解禁 的要求。
- 饰品波动通常大于股票，乖离率与 RSI 阈值宜更保守。"""

CS_TRADING_BASELINE_ZH = """## CS 饰品交易基线（与激活技能同时生效）
1. **严进**：现价相对 MA5 乖离过大（通常 >5%）时不建议追涨，优先观望或等回踩。
2. **趋势**：优先 MA5 ≥ MA10 ≥ MA20 的多头结构；显著空头排列降低看多权重。
3. **量能**：用 `volume_ratio_5d` 与 K 线 `volume` 判断放量/缩量；不用挂牌量代替成交量。
4. **买点**：缩量回踩 MA5/MA10 支撑优于追突破。
5. **风险**：数据质量非 full、量能可疑、或事件情报为空时，必须在结论中说明不确定性。"""

_CATEGORY_LABELS: Dict[str, str] = {
    "trend": "趋势",
    "pattern": "形态",
    "reversal": "反转",
    "framework": "框架",
}


@dataclass(frozen=True)
class CSSkillPromptState:
    active_skill_ids: tuple[str, ...]
    skill_instructions: str


def normalize_cs_skill_ids(skills: Optional[Sequence[str]]) -> List[str]:
    if not skills:
        return list(CS_DEFAULT_SKILL_IDS)
    normalized: List[str] = []
    for raw in skills:
        skill_id = str(raw or "").strip()
        if not skill_id or skill_id not in CS_ALLOWED_SKILL_IDS:
            if skill_id:
                logger.warning("CS skill ignored (not allowed): %s", skill_id)
            continue
        if skill_id not in normalized:
            normalized.append(skill_id)
    return normalized or list(CS_DEFAULT_SKILL_IDS)


def _load_cs_skill(skill_id: str) -> Optional[Skill]:
    cs_path = _CS_SKILLS_DIR / f"{skill_id}.yaml"
    if cs_path.is_file():
        return load_skill_from_yaml(cs_path)
    builtin_path = _BUILTIN_SKILLS_DIR / f"{skill_id}.yaml"
    if builtin_path.is_file():
        return load_skill_from_yaml(builtin_path)
    logger.warning("CS skill yaml not found: %s", skill_id)
    return None


def build_cs_skill_instructions(skill_ids: Sequence[str]) -> str:
    grouped: Dict[str, List[Skill]] = {}
    for skill_id in skill_ids:
        skill = _load_cs_skill(skill_id)
        if skill is None:
            continue
        category = skill.category or "trend"
        grouped.setdefault(category, []).append(skill)

    if not grouped:
        return ""

    parts: List[str] = []
    for category in ("trend", "pattern", "reversal", "framework"):
        skills = grouped.get(category) or []
        if not skills:
            continue
        label = _CATEGORY_LABELS.get(category, category)
        parts.append(f"### {label}类技能")
        for skill in skills:
            parts.append(f"#### {skill.display_name} (`{skill.name}`)")
            parts.append(skill.instructions.strip())
            parts.append("")
    return "\n".join(parts).strip()


def resolve_cs_skill_prompt(skills: Optional[Sequence[str]] = None) -> CSSkillPromptState:
    active = normalize_cs_skill_ids(skills)
    instructions = build_cs_skill_instructions(active)
    return CSSkillPromptState(
        active_skill_ids=tuple(active),
        skill_instructions=instructions,
    )


def list_cs_skills() -> List[Dict[str, str]]:
    """Metadata for Web/API skill picker (CS whitelist only)."""
    rows: List[Dict[str, str]] = []
    for skill_id in sorted(CS_ALLOWED_SKILL_IDS):
        skill = _load_cs_skill(skill_id)
        if skill is None:
            continue
        rows.append(
            {
                "id": skill.name,
                "display_name": skill.display_name,
                "description": skill.description,
                "category": skill.category or "trend",
                "source": "cs" if (_CS_SKILLS_DIR / f"{skill_id}.yaml").is_file() else "stock",
            }
        )
    rows.sort(key=lambda row: (row["category"], row["display_name"]))
    return rows


def fetch_cs_index_summary(*, sub_index_id: str = "1", period: int = 30) -> Dict[str, object]:
    """Light index context for dragon_head / relative-strength skills."""
    try:
        from market_provider.csqaq.client import CSQAQClient
        from market_provider.csqaq.ohlcv_adapter import index_kline_to_ohlcv

        bars = CSQAQClient().get_index_kline(sub_index_id=sub_index_id, period=period)
        frame = index_kline_to_ohlcv(bars)
        if frame.empty:
            return {}
        last = frame.iloc[-1]
        prev = frame.iloc[-2] if len(frame) > 1 else last
        prev_close = float(prev.get("close") or 0)
        close = float(last.get("close") or 0)
        daily_pct = ((close - prev_close) / prev_close * 100.0) if prev_close else 0.0
        return {
            "sub_index_id": str(sub_index_id),
            "period_days": int(period),
            "latest_date": str(last.get("date")),
            "latest_close": close,
            "daily_pct_chg": round(daily_pct, 2),
            "note": "指数成交量在免费 Token 下可能为 0，相对强弱以价格趋势为主",
        }
    except Exception as exc:
        logger.debug("CS index summary unavailable: %s", exc)
        return {}
