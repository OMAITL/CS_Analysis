# -*- coding: utf-8 -*-
"""Generate Markdown reports for CS item analysis (LLM + template fallback)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from market_provider.csqaq.item_analysis import CSItemAnalysisContext

logger = logging.getLogger(__name__)

def _template_report(ctx: CSItemAnalysisContext) -> str:
    t = ctx.trend
    snap = ctx.snapshot
    meta = ctx.meta
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    buff = snap.get("buff_sell_price")
    yyyp = snap.get("yyyp_sell_price")
    steam = snap.get("steam_sell_price")
    spread_lines = []
    if buff is not None and yyyp is not None:
        spread_lines.append(f"- BUFF {buff:.2f} vs 悠悠有品 {yyyp:.2f}（价差 {yyyp - buff:+.2f}）")
    if steam is not None and yyyp is not None:
        spread_lines.append(f"- Steam {steam:.2f} vs 悠悠有品 {yyyp:.2f}")

    reasons = "；".join(t.signal_reasons[:3]) if t.signal_reasons else "暂无"
    risks = "；".join(t.risk_factors[:4]) if t.risk_factors else "暂无"

    lines = [
        f"# CS 饰品分析报告：{ctx.item_name}",
        "",
        f"- **market_hash_name**: {ctx.market_hash_name}",
        f"- **good_id**: {ctx.good_id}",
        f"- **主平台**: {ctx.platform.upper()}",
        f"- **数据质量**: {meta.data_quality} | OHLC: {meta.ohlc_source} | 成交量: {meta.volume_source}",
        f"- **生成时间**: {now}",
        "",
        "> 本报告由规则模板生成（LLM 未配置或调用失败）。",
        "",
        "## 核心结论",
        "",
        f"当前趋势 **{t.trend_status.value}**，系统信号 **{t.buy_signal.value}**（评分 {t.signal_score}/100）。"
        f"最新价 **{t.current_price:.2f}**，5 日量比 **{t.volume_ratio_5d:.2f}**（{t.volume_status.value}）。",
        "",
        "## 技术面解读",
        "",
        f"- 均线：MA5={t.ma5:.2f} / MA10={t.ma10:.2f} / MA20={t.ma20:.2f} / MA60={t.ma60:.2f}",
        f"- 排列：{t.ma_alignment or '—'}",
        f"- 乖离率 MA5：{t.bias_ma5:.2f}%",
        f"- MACD：{t.macd_status.value}（DIF={t.macd_dif:.4f}, DEA={t.macd_dea:.4f}）",
        f"- RSI：{t.rsi_status.value}（6/12/24 = {t.rsi_6:.1f}/{t.rsi_12:.1f}/{t.rsi_24:.1f}）",
        f"- 依据：{reasons}",
        "",
        "## 平台价格与流动性",
        "",
    ]
    lines.extend(spread_lines or ["- 暂无多平台快照"])
    if snap.get("yyyp_sell_num") is not None:
        lines.append(f"- 悠悠有品挂牌量：**{snap['yyyp_sell_num']}**（≠ 成交量）")
    if snap.get("turnover_number") is not None:
        lines.append(f"- 当日 turnover 快照：{snap['turnover_number']}")
    lines.extend(["", "## 事件与舆论影响", ""])
    if ctx.event_context and ctx.event_context.strip():
        lines.append(ctx.event_context.strip())
    elif ctx.event_intel:
        for entry in ctx.event_intel[:8]:
            title = entry.get("title") or ""
            url = entry.get("url") or ""
            dim = entry.get("dimension") or ""
            lines.append(f"- [{dim}] {title}" + (f" ({url})" if url else ""))
    else:
        lines.append("- 近期未检索到高相关事件（搜索未配置或不可用）。")
    lines.extend(
        [
            "",
            "## 风险提示",
            "",
            risks,
            "",
            "## 操作建议",
            "",
            f"- **未持仓**：若信号为{t.buy_signal.value}，宜{'等待回调至 MA5/MA10 附近再评估' if t.bias_ma5 > 5 else '可小仓试探，严格止损'}。",
            f"- **已持仓**：趋势{t.trend_status.value}时可{'继续持有并移动止损' if '多头' in t.trend_status.value else '考虑减仓'}；关注 RSI 与量比变化。",
            "",
            "## 近期日 K（摘要）",
            "",
            "| 日期 | 收盘 | 成交量 |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in ctx.ohlcv_tail[-5:]:
        lines.append(f"| {row.get('date')} | {float(row.get('close') or 0):.2f} | {float(row.get('volume') or 0):.0f} |")
    lines.append("")
    return "\n".join(lines)


class CSItemReportGenerator:
    """Generate Markdown report via LLM with deterministic template fallback."""

    def __init__(self, *, analyzer=None) -> None:
        if analyzer is None:
            from src.analyzer import GeminiAnalyzer

            analyzer = GeminiAnalyzer()
        self._analyzer = analyzer

    def generate(
        self,
        ctx: CSItemAnalysisContext,
        *,
        skills: Optional[Sequence[str]] = None,
        index_summary: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.5,
    ) -> tuple[str, str]:
        """
        Returns (markdown, source) where source is ``llm`` or ``template``.

        Skills are applied at ``GeminiAnalyzer.analyze()`` (JSON dashboard), same as stocks.
        ``max_tokens`` / ``temperature`` are kept for CLI compatibility but ignored on this path.
        """
        del max_tokens, temperature, index_summary
        from src.services.cs_analysis_report import run_cs_item_llm_analysis

        markdown, source, _active = run_cs_item_llm_analysis(
            ctx,
            skills=skills,
            analyzer=self._analyzer,
        )
        return markdown, source
