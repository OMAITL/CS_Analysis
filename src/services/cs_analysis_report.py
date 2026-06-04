# -*- coding: utf-8 -*-
"""CS item analysis via stock-equivalent GeminiAnalyzer.analyze() (JSON dashboard)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from market_provider.csqaq.item_analysis import CSItemAnalysisContext
from src.analyzer import AnalysisResult, GeminiAnalyzer
from src.report_language import normalize_report_language
from src.services.cs_skill_prompt import (
    CS_SKILL_DATA_MAPPING,
    CS_TRADING_BASELINE_ZH,
    fetch_cs_index_summary,
    resolve_cs_skill_prompt,
)

logger = logging.getLogger(__name__)

CS_MARKET_ROLE_ZH = "CS2（Counter-Strike 2）饰品市场"
CS_MARKET_ROLE_EN = "CS2 (Counter-Strike 2) skin market"

CS_MARKET_GUIDELINES_ZH = """- 分析对象为 CS2 饰品价格与 K 线成交，不是股票；无 PE/财报/涨停/板块排名/筹码分布。
- `volume` 为 K 线日成交笔数；`buff_sell_num`/`yyyp_sell_num` 为挂牌量，**不是**成交量。
- 事件情报仅可引用输入中的 `event_intel` / 舆情块；禁止编造新闻。
- 饰品波动通常大于股票，乖离率与 RSI 阈值宜更保守。
- `chip_structure` 可填 null 或说明「饰品无筹码分布」；`turnover_rate` 可填 null。"""

CS_MARKET_GUIDELINES_EN = """- Analyze CS2 skin prices and K-line volume, not equities; no P/E, earnings, price limits, or chip distribution.
- `volume` is daily trade count from K-line; listing counts are not volume.
- Use only event intel provided in the prompt; do not invent news.
- Skin volatility is typically higher than stocks; use conservative bias/RSI thresholds.
- Set `chip_structure` to null or note unavailable; `turnover_rate` may be null."""

CS_JSON_FIELD_NOTE_ZH = (
    '- JSON 中 `stock_name` 填饰品中文名；`code` 保持输入中的 cs:good_id 形式。\n'
    "- `operation_advice` 可用：买入/加仓/持有/减仓/卖出/观望（饰品语义）。\n"
    "- 平台价格、挂牌量写入 `dashboard.data_perspective` 或 `intelligence` 相关叙述。"
)

CS_JSON_FIELD_NOTE_EN = (
    "- Use item display name for `stock_name`; keep `code` as cs:good_id.\n"
    "- `operation_advice` may use buy/hold/sell style labels adapted for skins.\n"
    "- Reflect multi-platform prices and listing depth in dashboard narrative fields."
)


def _needs_index_summary(skills: Optional[Sequence[str]]) -> bool:
    if not skills:
        return False
    return any(str(s).strip() == "dragon_head" for s in skills)


def build_cs_gemini_analyzer(
    skills: Optional[Sequence[str]] = None,
    *,
    analyzer: Optional[GeminiAnalyzer] = None,
) -> Tuple[GeminiAnalyzer, object]:
    """GeminiAnalyzer with CS skill sections resolved at system-prompt time (stock path)."""
    skill_state = resolve_cs_skill_prompt(skills)
    instructions = CS_SKILL_DATA_MAPPING
    if skill_state.skill_instructions:
        instructions = f"{instructions}\n\n{skill_state.skill_instructions}"
    instance = analyzer or GeminiAnalyzer(
        skill_instructions=instructions,
        default_skill_policy=CS_TRADING_BASELINE_ZH,
        use_legacy_default_prompt=False,
    )
    return instance, skill_state


def build_cs_analyzer_context(
    ctx: CSItemAnalysisContext,
    *,
    index_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Map CS fused context to the dict consumed by GeminiAnalyzer.analyze()."""
    trend = ctx.trend
    tail = list(ctx.ohlcv_tail or [])
    today_bar = tail[-1] if tail else {}
    yesterday_bar = tail[-2] if len(tail) >= 2 else {}

    def _bar_slice(bar: Dict[str, Any]) -> Dict[str, Any]:
        if not bar:
            return {}
        close = float(bar.get("close") or 0)
        return {
            "close": close,
            "open": float(bar.get("open") or close),
            "high": float(bar.get("high") or close),
            "low": float(bar.get("low") or close),
            "volume": float(bar.get("volume") or 0),
            "pct_chg": bar.get("change_percent") or bar.get("pct_chg"),
            "ma5": trend.ma5,
            "ma10": trend.ma10,
            "ma20": trend.ma20,
            "date": bar.get("date"),
        }

    snap = ctx.snapshot
    realtime: Dict[str, Any] = {
        "name": ctx.item_name,
        "price": trend.current_price,
        "volume_ratio": trend.volume_ratio_5d,
        "volume_ratio_desc": trend.volume_status.value,
    }
    buff = snap.get("buff_sell_price")
    yyyp = snap.get("yyyp_sell_price")
    if buff is not None:
        realtime["buff_sell_price"] = buff
    if yyyp is not None:
        realtime["yyyp_sell_price"] = yyyp
    if snap.get("yyyp_sell_num") is not None:
        realtime["yyyp_sell_num"] = snap.get("yyyp_sell_num")
    if snap.get("buff_sell_num") is not None:
        realtime["buff_sell_num"] = snap.get("buff_sell_num")

    payload: Dict[str, Any] = {
        "asset_type": "cs_item",
        "is_cs_item": True,
        "code": f"cs:{ctx.good_id}",
        "stock_name": ctx.item_name,
        "market_hash_name": ctx.market_hash_name,
        "platform": ctx.platform,
        "date": str(today_bar.get("date") or ""),
        "today": _bar_slice(today_bar),
        "yesterday": _bar_slice(yesterday_bar),
        "ma_status": trend.ma_alignment,
        "realtime": realtime,
        "trend_analysis": {
            "trend_status": trend.trend_status.value,
            "ma_alignment": trend.ma_alignment,
            "trend_strength": trend.trend_strength,
            "bias_ma5": trend.bias_ma5,
            "bias_ma10": getattr(trend, "bias_ma10", 0.0),
            "volume_status": trend.volume_status.value,
            "volume_trend": getattr(trend, "volume_trend", ""),
            "buy_signal": trend.buy_signal.value,
            "signal_score": trend.signal_score,
            "signal_reasons": list(trend.signal_reasons or []),
            "risk_factors": list(trend.risk_factors or []),
            "macd_status": trend.macd_status.value,
            "rsi_status": trend.rsi_status.value,
        },
        "data_meta": ctx.meta.model_dump(mode="json"),
        "cs_snapshot": {
            key: snap.get(key)
            for key in (
                "buff_sell_price",
                "yyyp_sell_price",
                "steam_sell_price",
                "buff_sell_num",
                "yyyp_sell_num",
                "turnover_number",
                "updated_at",
            )
            if snap.get(key) is not None
        },
        "recent_daily_bars": tail,
        "event_intel": list(ctx.event_intel or []),
    }
    if index_summary:
        payload["index_summary"] = index_summary
    return payload


def format_cs_analyzer_user_prompt(
    context: Dict[str, Any],
    name: str,
    news_context: Optional[str] = None,
    *,
    report_language: str = "zh",
) -> str:
    """User prompt for CS JSON dashboard analysis (skills live in system prompt)."""
    lang = normalize_report_language(report_language)
    code = context.get("code", "cs:unknown")
    item_name = context.get("stock_name") or name
    meta = context.get("data_meta") or {}
    trend = context.get("trend_analysis") or {}
    unknown = "Unknown" if lang == "en" else "未知"

    lines = [
        "# CS 饰品决策仪表盘分析请求" if lang == "zh" else "# CS Item Decision Dashboard Request",
        "",
        "## 标的" if lang == "zh" else "## Instrument",
        f"| {'项目' if lang == 'zh' else 'Field'} | {'数据' if lang == 'zh' else 'Value'} |",
        "|------|------|",
        f"| {'名称' if lang == 'zh' else 'Name'} | **{item_name}** |",
        f"| market_hash_name | {context.get('market_hash_name', unknown)} |",
        f"| good_id / code | **{code}** |",
        f"| {'主平台' if lang == 'zh' else 'Platform'} | {context.get('platform', unknown)} |",
        f"| {'分析日期' if lang == 'zh' else 'Date'} | {context.get('date', unknown)} |",
        f"| {'数据质量' if lang == 'zh' else 'Data quality'} | {meta.get('data_quality', unknown)} |",
        "",
        "## 结构化 payload（JSON）",
        "",
        f"```json\n{json.dumps({k: context[k] for k in context if k not in ('asset_type', 'is_cs_item')}, ensure_ascii=False, indent=2)}\n```",
        "",
    ]

    if trend:
        lines.extend(
            [
                "## 系统趋势摘要（预计算）",
                "",
                f"- {'趋势' if lang == 'zh' else 'Trend'}: {trend.get('trend_status', unknown)}",
                f"- {'均线' if lang == 'zh' else 'MA'}: {trend.get('ma_alignment', unknown)}",
                f"- {'信号' if lang == 'zh' else 'Signal'}: {trend.get('buy_signal', unknown)} ({trend.get('signal_score', 0)}/100)",
                f"- {'量比状态' if lang == 'zh' else 'Volume'}: {trend.get('volume_status', unknown)}",
                "",
            ]
        )

    lines.append("---")
    lines.append("")
    lines.append("## 事件与舆论情报" if lang == "zh" else "## Event & sentiment intel")
    if news_context and news_context.strip():
        lines.extend(["", news_context.strip(), ""])
    else:
        lines.append(
            "\n未提供事件检索正文；请依据 `event_intel` JSON，无内容时 intelligence 区说明未检索到。\n"
            if lang == "zh"
            else "\nNo event search text; use event_intel JSON only.\n"
        )

    task = (
        f"\n---\n\n请为 **{item_name}** 生成【决策仪表盘】JSON（与股票分析相同 schema）。"
        f"{CS_JSON_FIELD_NOTE_ZH if lang == 'zh' else CS_JSON_FIELD_NOTE_EN}"
    )
    lines.append(task)
    return "\n".join(lines)


def get_cs_analysis_system_prompt(
    analyzer: GeminiAnalyzer,
    report_language: str,
) -> str:
    """Build system prompt with skills injected like stock analyze() path."""
    lang = normalize_report_language(report_language)
    role = CS_MARKET_ROLE_EN if lang == "en" else CS_MARKET_ROLE_ZH
    guidelines = CS_MARKET_GUIDELINES_EN if lang == "en" else CS_MARKET_GUIDELINES_ZH
    skill_instructions, default_skill_policy, use_legacy = analyzer._get_skill_prompt_sections()
    if use_legacy:
        base_prompt = analyzer.LEGACY_DEFAULT_SYSTEM_PROMPT.replace(
            "{market_placeholder}", role
        ).replace("{guidelines_placeholder}", guidelines)
    else:
        skills_section = ""
        if skill_instructions:
            skills_section = f"## 激活的交易技能\n\n{skill_instructions}\n"
        policy_section = f"{default_skill_policy}\n" if default_skill_policy else ""
        base_prompt = (
            analyzer.SYSTEM_PROMPT.replace("{market_placeholder}", role)
            .replace("{guidelines_placeholder}", guidelines)
            .replace("{default_skill_policy_section}", policy_section)
            .replace("{skills_section}", skills_section)
        )
    if lang == "en":
        return base_prompt + """

## Output Language (highest priority)

- Keep all JSON keys unchanged.
- `decision_type` must remain `buy|hold|sell`.
- All human-readable JSON values must be written in English.
"""
    return base_prompt + """

## 输出语言（最高优先级）

- 所有 JSON 键名保持不变。
- `decision_type` 必须保持为 `buy|hold|sell`。
- 所有面向用户的人类可读文本值必须使用中文。
"""


def analysis_result_to_cs_markdown(
    result: AnalysisResult,
    ctx: CSItemAnalysisContext,
) -> str:
    """Render stock-style AnalysisResult JSON into CS Web Markdown sections."""
    dash = result.dashboard if isinstance(result.dashboard, dict) else {}
    core = dash.get("core_conclusion") or {}
    intel = dash.get("intelligence") or {}
    data_p = dash.get("data_perspective") or {}
    battle = dash.get("battle_plan") or {}
    pos = core.get("position_advice") or {}
    sniper = battle.get("sniper_points") or {}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = ctx.meta
    t = ctx.trend
    snap = ctx.snapshot

    one_sentence = core.get("one_sentence") or result.analysis_summary or "—"
    lines = [
        f"# CS 饰品分析报告：{ctx.item_name}",
        "",
        f"- **market_hash_name**: {ctx.market_hash_name}",
        f"- **good_id**: {ctx.good_id}",
        f"- **主平台**: {ctx.platform.upper()}",
        f"- **综合评分**: {result.sentiment_score}/100 | **建议**: {result.operation_advice} | **趋势**: {result.trend_prediction}",
        f"- **数据质量**: {meta.data_quality} | 生成时间: {now}",
        "",
        "> 本报告由 LLM 决策仪表盘 JSON 渲染（与股票分析同一介入点）。",
        "",
        "## 核心结论",
        "",
        one_sentence,
        "",
    ]
    if pos.get("no_position") or pos.get("has_position"):
        if pos.get("no_position"):
            lines.append(f"- **未持仓**：{pos['no_position']}")
        if pos.get("has_position"):
            lines.append(f"- **已持仓**：{pos['has_position']}")
        lines.append("")

    lines.extend(["## 技术面解读", ""])
    for key, label in (
        ("technical_analysis", "技术面"),
        ("ma_analysis", "均线"),
        ("volume_analysis", "量能"),
        ("pattern_analysis", "形态"),
        ("trend_analysis", "走势"),
    ):
        text = getattr(result, key, None) or ""
        if text:
            lines.append(f"**{label}**：{text}")
    price_pos = data_p.get("price_position") or {}
    if price_pos:
        lines.append(
            f"- 价位：现价 {price_pos.get('current_price', t.current_price)} | "
            f"支撑 {price_pos.get('support_level', '—')} | 压力 {price_pos.get('resistance_level', '—')}"
        )
    vol = data_p.get("volume_analysis") or {}
    if vol:
        lines.append(f"- 量能：{vol.get('volume_status', t.volume_status.value)} — {vol.get('volume_meaning', '')}")
    lines.append(
        f"- 系统预计算：{t.trend_status.value} / {t.buy_signal.value}（{t.signal_score}/100）"
    )
    lines.append("")

    lines.extend(["## 平台价格与流动性", ""])
    spread = []
    buff = snap.get("buff_sell_price")
    yyyp = snap.get("yyyp_sell_price")
    if buff is not None and yyyp is not None:
        spread.append(f"- BUFF {buff:.2f} vs 悠悠有品 {yyyp:.2f}")
    if spread:
        lines.extend(spread)
    else:
        lines.append(f"- 现价参考：{t.current_price:.2f}")
    if snap.get("yyyp_sell_num") is not None:
        lines.append(f"- 悠悠有品挂牌量：**{snap['yyyp_sell_num']}**（≠ 成交量）")
    lines.append("")

    lines.extend(["## 事件与舆论影响", ""])
    if intel.get("sentiment_summary"):
        lines.append(intel["sentiment_summary"])
    if intel.get("latest_news"):
        lines.append(f"\n{intel['latest_news']}")
    for alert in intel.get("risk_alerts") or []:
        lines.append(f"- ⚠️ {alert}")
    for cat in intel.get("positive_catalysts") or []:
        lines.append(f"- ✨ {cat}")
    if result.news_summary:
        lines.append(f"\n{result.news_summary}")
    if ctx.event_context and ctx.event_context.strip() and not intel:
        lines.append(ctx.event_context.strip())
    elif ctx.event_intel and not intel:
        for entry in ctx.event_intel[:8]:
            title = entry.get("title") or ""
            url = entry.get("url") or ""
            lines.append(f"- {title}" + (f" ({url})" if url else ""))
    if not intel and not ctx.event_intel and not ctx.event_context:
        lines.append("- 近期未检索到高相关事件。")
    lines.append("")

    lines.extend(["## 风险提示", ""])
    risks = intel.get("risk_alerts") or []
    if result.risk_warning:
        lines.append(result.risk_warning)
    elif risks:
        lines.extend(f"- {r}" for r in risks)
    elif t.risk_factors:
        lines.extend(f"- {r}" for r in t.risk_factors[:6])
    else:
        lines.append("- 请结合数据质量与波动自行控制仓位。")
    lines.append("")

    lines.extend(["## 操作建议", ""])
    if battle.get("action_plan"):
        lines.append(battle["action_plan"])
    if sniper:
        for label, key in (
            ("理想买入", "ideal_entry"),
            ("止损", "stop_loss"),
            ("目标", "target"),
        ):
            if sniper.get(key):
                lines.append(f"- **{label}**：{sniper[key]}")
    if result.buy_reason:
        lines.append(f"\n**理由**：{result.buy_reason}")
    lines.append("")

    return "\n".join(lines)


def _extract_containers(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for entry in snapshot.get("container") or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        row: Dict[str, Any] = {"name": name}
        if entry.get("id") is not None:
            row["good_id"] = int(entry["id"])
        price = entry.get("price")
        if price is not None:
            try:
                row["price"] = float(price)
            except (TypeError, ValueError):
                pass
        rows.append(row)
    return rows


def _fmt_price(value: float) -> str:
    return f"{value:.2f}"


def build_cs_report_payload(
    ctx: CSItemAnalysisContext,
    result: Optional[AnalysisResult] = None,
) -> Dict[str, Any]:
    """Structured dashboard payload for Web (stock ReportSummary equivalent)."""
    trend = ctx.trend
    meta = ctx.meta

    if result and result.success:
        dash = result.dashboard if isinstance(result.dashboard, dict) else {}
        core = dash.get("core_conclusion") or {}
        analysis_summary = str(
            core.get("one_sentence") or result.analysis_summary or ""
        ).strip()
        operation_advice = str(result.operation_advice or trend.buy_signal.value).strip()
        trend_prediction = str(result.trend_prediction or trend.trend_status.value).strip()
        try:
            sentiment_score = int(result.sentiment_score or trend.signal_score or 50)
        except (TypeError, ValueError):
            sentiment_score = int(trend.signal_score or 50)

        sniper = {}
        if hasattr(result, "get_sniper_points"):
            sniper = result.get_sniper_points() or {}
        if not sniper:
            battle = dash.get("battle_plan") or {}
            sniper = battle.get("sniper_points") or {}

        data_p = dash.get("data_perspective") or {}
        price_pos = data_p.get("price_position") or data_p.get("price_perspective") or {}
        support = price_pos.get("support_level")
        resistance = price_pos.get("resistance_level")
    else:
        reasons = "；".join(trend.signal_reasons[:2]) if trend.signal_reasons else ""
        analysis_summary = reasons or (
            f"{trend.trend_status.value}，系统信号 {trend.buy_signal.value}（{trend.signal_score}/100）"
        )
        operation_advice = trend.buy_signal.value
        trend_prediction = trend.trend_status.value
        sentiment_score = int(trend.signal_score or 50)
        sniper = {}
        support = resistance = None

    strategy = {
        "ideal_buy": sniper.get("ideal_buy")
        or (f"MA5 附近 {_fmt_price(trend.ma5)}" if trend.ma5 else None),
        "secondary_buy": sniper.get("secondary_buy")
        or (f"MA10 附近 {_fmt_price(trend.ma10)}" if trend.ma10 else None),
        "stop_loss": sniper.get("stop_loss")
        or (f"跌破 MA20 {_fmt_price(trend.ma20)}" if trend.ma20 else None),
        "take_profit": sniper.get("take_profit")
        or (str(resistance) if resistance else None),
    }

    containers = _extract_containers(ctx.snapshot)
    belong_boards = [
        {
            "name": row["name"],
            "type": "武器箱",
            "code": str(row.get("good_id") or ""),
        }
        for row in containers
    ]

    quality = str(meta.data_quality or "unknown")
    if quality == "full":
        diag_status = "normal"
        diag_reason = "K 线 OHLCV 与成交量来源可靠，可用于趋势与量比判断。"
    elif quality in {"degraded", "mixed"}:
        diag_status = "degraded"
        diag_reason = f"数据质量为 {quality}，成交量或 OHLC 存在降级，结论需保守解读。"
    else:
        diag_status = "degraded"
        diag_reason = f"数据质量为 {quality}，主要依赖价格序列，量能信号可信度下降。"

    crawl_status = "ok" if int(meta.crawl_rows or 0) > 0 else "degraded"
    crawl_msg = (
        f"爬虫 K 线 {meta.crawl_rows} 条（{meta.ohlc_source}）"
        if int(meta.crawl_rows or 0) > 0
        else "未命中爬虫 K 线，已回退 API 价格序列"
    )
    intel_count = len(ctx.event_intel or [])
    intel_status = "ok" if intel_count > 0 else "skipped"
    llm_status = "ok" if result and result.success else "skipped"

    components = {
        "csqaq_api": {
            "key": "csqaq_api",
            "label": "CSQAQ 数据",
            "status": "ok",
            "message": f"API 序列 {meta.api_rows} 条，平台 {ctx.platform.upper()}",
        },
        "kline_crawl": {
            "key": "kline_crawl",
            "label": "K 线融合",
            "status": crawl_status,
            "message": crawl_msg,
        },
        "event_intel": {
            "key": "event_intel",
            "label": "事件情报",
            "status": intel_status,
            "message": f"检索到 {intel_count} 条展示情报" if intel_count else "未配置或未命中相关事件",
        },
        "llm_report": {
            "key": "llm_report",
            "label": "LLM 报告",
            "status": llm_status,
            "message": "决策仪表盘 JSON 已生成" if llm_status == "ok" else "已降级为规则模板",
        },
    }

    status_labels = {
        "normal": "正常",
        "degraded": "部分降级",
        "failed": "失败",
        "unknown": "未知",
    }

    return {
        "summary": {
            "analysis_summary": analysis_summary,
            "operation_advice": operation_advice,
            "trend_prediction": trend_prediction,
            "sentiment_score": max(0, min(100, sentiment_score)),
        },
        "strategy": strategy,
        "diagnostics": {
            "status": diag_status,
            "status_label": status_labels.get(diag_status, diag_status),
            "reason": diag_reason,
            "components": components,
            "copy_text": (
                f"CS good_id={ctx.good_id} quality={quality} "
                f"signal={operation_advice} score={sentiment_score}"
            ),
        },
        "containers": containers,
        "belong_boards": belong_boards,
    }


def run_cs_item_llm_analysis(
    ctx: CSItemAnalysisContext,
    *,
    skills: Optional[Sequence[str]] = None,
    analyzer: Optional[GeminiAnalyzer] = None,
) -> Tuple[str, str, Tuple[str, ...], Optional[AnalysisResult]]:
    """
    Run GeminiAnalyzer.analyze() for CS and return (markdown, source, active_skill_ids, result).
    """
    from market_provider.csqaq.cs_report import _template_report

    skill_state = resolve_cs_skill_prompt(skills)
    active = skill_state.active_skill_ids
    index_summary = None
    if _needs_index_summary(active):
        index_summary = fetch_cs_index_summary()

    gemini, _ = build_cs_gemini_analyzer(skills, analyzer=analyzer)
    if not gemini.is_available():
        return _template_report(ctx), "template", active, None

    context = build_cs_analyzer_context(ctx, index_summary=index_summary)
    news = (ctx.event_context or "").strip() or None
    try:
        result = gemini.analyze(context, news_context=news)
    except Exception as exc:
        logger.warning("CS item analyze() failed: %s", exc)
        return _template_report(ctx), "template", active, None

    if not result.success:
        logger.warning("CS item analyze() unsuccessful: %s", result.error_message)
        return _template_report(ctx), "template", active, result

    return analysis_result_to_cs_markdown(result, ctx), "llm", active, result
