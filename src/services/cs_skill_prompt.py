# -*- coding: utf-8 -*-
"""Load stock trading skills for CS item LLM reports (prompt injection only)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

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

CS_SKILL_DATA_MAPPING = """## CS 技能与 Agent 工具映射（必须遵守）
- `search_cs_item`：按饰品名搜索 good_id；多磨损档时须确认后再分析
- `analyze_cs_item`：获取 trend（≈ analyze_trend）、recent_daily_bars（≈ K 线 OHLCV）、各平台价格快照
- `search_cs_item_intel`：事件/新闻情报（≈ 综合情报，无财报/公告）
- `get_cs_market_overview`：饰品指数/子板块；`include_watchlist=true` 时返回市场扫描候选
- `get_cs_portfolio_snapshot`：用户 CS 持仓快照
- `snapshot` 中各平台价格 ≈ 现价/挂牌参考；K 线 `volume` 为日成交笔数，`sell_num` 仅为挂牌量
- 忽略技能原文中：筹码分布、换手率、涨停、板块排名、PE/财报、减持/解禁 等股票专用要求
- 饰品波动通常大于股票，乖离率与 RSI 阈值宜更保守"""

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


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compact_sub_index_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize CSQAQ ``sub_index_data`` row from ``/api/v1/current_data``."""
    chg_rate = _safe_float(row.get("chg_rate"))
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "market_index": _safe_float(row.get("market_index")),
        "chg_num": _safe_float(row.get("chg_num")),
        "chg_rate": chg_rate,
        "change_pct": chg_rate,
        "open": _safe_float(row.get("open")),
        "close": _safe_float(row.get("close")),
        "high": _safe_float(row.get("high")),
        "low": _safe_float(row.get("low")),
        "updated_at": row.get("updated_at"),
    }


def fetch_cs_home_market(*, sub_index_limit: int = 6) -> Dict[str, Any]:
    """Dashboard snapshot aligned with https://csqaq.com/home sub-index cards."""
    try:
        from market_provider.csqaq.client import CSQAQClient

        rows = [
            compact_sub_index_row(dict(row))
            for row in (CSQAQClient().list_sub_indexes() or [])
            if isinstance(row, dict)
        ]
        if not rows:
            return {}
        main = next((row for row in rows if str(row.get("id")) == "1"), rows[0])
        return {
            "main_index": main,
            "sub_indexes": rows[: max(1, int(sub_index_limit))],
            "updated_at": main.get("updated_at"),
        }
    except Exception as exc:
        logger.debug("CS home market unavailable: %s", exc)
        return {}


def _compact_rank_row(row: Dict[str, Any]) -> Dict[str, Any]:
    pct = (
        row.get("buff_price_chg")
        or row.get("price_diff")
        or row.get("price_diff_7")
        or row.get("change_pct")
        or row.get("pct_chg")
        or row.get("rank_rate")
        or row.get("chg_rate")
    )
    price = (
        row.get("yyyp_sell_price")
        or row.get("sell_price")
        or row.get("price")
        or row.get("buff_sell_price")
    )
    return {
        "good_id": row.get("good_id") or row.get("id"),
        "name": row.get("name") or row.get("item_name"),
        "price": _safe_float(price),
        "change_pct": _safe_float(pct),
        "sell_num": row.get("yyyp_sell_num") or row.get("sell_num"),
    }


def _fetch_cs_rank_leaders_via_browser(
    *,
    day_type: int,
    limit: int,
) -> Dict[str, Any]:
    from crawlers.csqaq.browser_crawler import CSQAQBrowserCrawler

    browser_payload = CSQAQBrowserCrawler().fetch_rank_leaders(day_type=day_type, limit=limit)
    return {
        "day_type": int(day_type),
        "limit": int(limit),
        "gainers": [
            _compact_rank_row(dict(row))
            for row in (browser_payload.get("gainers") or [])
            if isinstance(row, dict)
        ],
        "losers": [
            _compact_rank_row(dict(row))
            for row in (browser_payload.get("losers") or [])
            if isinstance(row, dict)
        ],
        "source": browser_payload.get("source") or "browser_rank_page",
    }


def fetch_cs_rank_leaders(
    *,
    day_type: int = 7,
    limit: int = 5,
) -> Dict[str, Any]:
    """Top gainers/losers (%) from https://csqaq.com/rank (近7天 by default)."""
    payload: Dict[str, Any] = {
        "day_type": int(day_type),
        "limit": int(limit),
        "gainers": [],
        "losers": [],
    }
    api_error: Optional[str] = None
    try:
        from market_provider.csqaq.client import CSQAQClient

        client = CSQAQClient(timeout=8.0)
        for rank_type, key in ((1, "gainers"), (2, "losers")):
            try:
                response = client.get_rank_list(
                    rank_type=rank_type,
                    day_type=day_type,
                    page_index=1,
                    page_size=max(1, int(limit)),
                )
                rows = list(response.get("data") or response.get("list") or [])
                if isinstance(response.get("data"), dict):
                    rows = list(response["data"].get("data") or [])
                payload[key] = [
                    _compact_rank_row(dict(row))
                    for row in rows[: max(1, int(limit))]
                    if isinstance(row, dict)
                ]
            except Exception as exc:
                api_error = str(exc)
                logger.warning("CS rank API fetch failed rank_type=%s: %s", rank_type, exc)
    except Exception as exc:
        api_error = str(exc)
        logger.debug("CS rank API unavailable: %s", exc)

    if payload["gainers"] or payload["losers"]:
        payload["source"] = "csqaq_api"
        return payload

    try:
        browser_payload = _fetch_cs_rank_leaders_via_browser(day_type=day_type, limit=limit)
        if browser_payload.get("gainers") or browser_payload.get("losers"):
            return browser_payload
        payload["error"] = api_error or "rank list empty from browser"
        return payload
    except ImportError as exc:
        logger.warning("CS rank browser fallback unavailable (playwright): %s", exc)
        payload["error"] = api_error or str(exc)
        return payload
    except Exception as exc:
        logger.warning("CS rank browser fallback failed: %s", exc)
        payload["error"] = api_error or str(exc)
        return payload


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
