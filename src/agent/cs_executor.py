# -*- coding: utf-8 -*-
"""CS item chat Agent — ReAct loop with CS tools (same mode as stock 问股)."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from src.agent.chat_context import build_visible_chat_history
from src.agent.executor import AgentExecutor, AgentResult
from src.agent.runner import run_agent_loop
from src.config import get_config

logger = logging.getLogger(__name__)

CS_CHAT_SYSTEM_PROMPT = """你是 CS2（Counter-Strike 2）饰品投资分析 Agent，拥有 CS 专用数据工具与可切换交易技能，负责解答用户的饰品投资问题。

## 分析工作流程（必须严格按阶段执行，禁止跳步）

当用户询问某个具体饰品时：

**第一阶段 · 解析饰品**
- 若上下文或用户已给出 `good_id`，记录并进入第二阶段
- 否则调用 `search_cs_item` 按名称解析 good_id
- 若返回多个磨损档（崭新/略磨/久经等）且用户未指定，必须在回答中列出候选并说明当前分析使用的是哪一档；不要擅自换成其他磨损档

**第二阶段 · 拉数与技术**
- 调用 `analyze_cs_item` 获取 K 线、平台价格、趋势指标（MA/MACD/RSI/信号分等）
- 所有数字必须来自工具返回，禁止编造

**第三阶段 · 情报（按需）**
- 需要事件/新闻/箱子/赛事情境时调用 `search_cs_item_intel`

**第四阶段 · 综合回答**
- 结合激活技能给出结论：**先结论，后依据**
- 用户问买/卖/持有/做盘/风险时，必须基于第二阶段真实数据

## 其他场景
- 全市场/哪些饰品可能做盘：调用 `get_cs_market_overview(include_watchlist=true)`，只能引用工具返回的 `authorized_items`
- 我的持仓：调用 `get_cs_portfolio_snapshot`

## 规则
1. **必须调用工具** — 不得在未调用 `analyze_cs_item` 的情况下对具体饰品给出量化结论
2. **禁止股票概念** — 不用 PE、财报、涨停、筹码分布等股票专用术语
3. **volume 语义** — K 线 `volume` 是日成交笔数；`sell_num` 是挂牌量
4. **工具失败** — 说明原因，不要要求用户「去首页点分析」；可建议检查 CSQAQ Token/IP 白名单
5. **自由对话** — 用 Markdown，结构清晰，不需要输出 JSON

{data_mapping}

{baseline}

{skills_section}
"""

CS_THINKING_TOOL_LABELS: Dict[str, str] = {
    "search_cs_item": "检索饰品 good_id",
    "analyze_cs_item": "拉取 K 线与技术指标",
    "search_cs_item_intel": "搜索饰品事件情报",
    "get_cs_market_overview": "获取市场指数/扫描",
    "get_cs_portfolio_snapshot": "读取持仓快照",
}


class CSAgentExecutor(AgentExecutor):
    """ReAct agent for CS item chat — mirrors stock AgentExecutor.chat behaviour."""

    def __init__(
        self,
        *,
        tool_registry,
        llm_adapter,
        skill_instructions: str = "",
        data_mapping: str = "",
        baseline: str = "",
        max_steps: int = 10,
        timeout_seconds: Optional[float] = None,
    ):
        super().__init__(
            tool_registry=tool_registry,
            llm_adapter=llm_adapter,
            skill_instructions=skill_instructions,
            default_skill_policy="",
            use_legacy_default_prompt=False,
            max_steps=max_steps,
            timeout_seconds=timeout_seconds,
        )
        self.data_mapping = data_mapping
        self.baseline = baseline

    def chat(
        self,
        message: str,
        session_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        from src.agent.conversation import conversation_manager

        skills_section = ""
        if self.skill_instructions:
            skills_section = f"## 激活的交易技能\n\n{self.skill_instructions}"

        system_prompt = CS_CHAT_SYSTEM_PROMPT.format(
            data_mapping=self.data_mapping or "",
            baseline=self.baseline or "",
            skills_section=skills_section,
        )

        tool_decls = self.tool_registry.to_openai_tools()
        conversation_manager.get_or_create(session_id)
        config = getattr(self.llm_adapter, "_config", None) or get_config()
        history = build_visible_chat_history(session_id, self.llm_adapter, config)

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        ctx = dict(context or {})
        ctx.pop("scope", None)
        if ctx:
            context_parts: List[str] = []
            if ctx.get("good_id") is not None:
                context_parts.append(f"关联 good_id: {ctx['good_id']}")
            if ctx.get("item_name"):
                context_parts.append(f"关联饰品名: {ctx['item_name']}")
            if ctx.get("platform"):
                context_parts.append(f"平台偏好: {ctx['platform']}")
            if ctx.get("previous_analysis_summary"):
                summary = ctx["previous_analysis_summary"]
                summary_text = (
                    json.dumps(summary, ensure_ascii=False)
                    if isinstance(summary, dict)
                    else str(summary)
                )
                context_parts.append(f"上次分析摘要:\n{summary_text}")
            if context_parts:
                context_msg = "[系统提供的历史分析上下文，可供参考；若用户提到新饰品名，以新饰品为准]\n" + "\n".join(
                    context_parts
                )
                messages.append({"role": "user", "content": context_msg})
                messages.append(
                    {
                        "role": "assistant",
                        "content": "好的，我已了解历史上下文。我会先调用工具解析并拉取最新数据，再回答你的问题。",
                    }
                )

        messages.append({"role": "user", "content": message})
        conversation_manager.add_message(session_id, "user", message)

        result = self._run_loop(
            messages,
            tool_decls,
            parse_dashboard=False,
            progress_callback=progress_callback,
            thinking_labels=CS_THINKING_TOOL_LABELS,
        )

        if result.success:
            conversation_manager.add_message(session_id, "assistant", result.content)
        else:
            error_note = f"[分析失败] {result.error or '未知错误'}"
            conversation_manager.add_message(session_id, "assistant", error_note)

        return result

    def _run_loop(
        self,
        messages: List[Dict[str, Any]],
        tool_decls: List[Dict[str, Any]],
        parse_dashboard: bool,
        progress_callback: Optional[Callable] = None,
        thinking_labels: Optional[Dict[str, str]] = None,
    ) -> AgentResult:
        loop_result = run_agent_loop(
            messages=messages,
            tool_registry=self.tool_registry,
            llm_adapter=self.llm_adapter,
            max_steps=self.max_steps,
            progress_callback=progress_callback,
            thinking_labels=thinking_labels or CS_THINKING_TOOL_LABELS,
            max_wall_clock_seconds=self.timeout_seconds,
        )

        return AgentResult(
            success=loop_result.success,
            content=loop_result.content,
            tool_calls_log=loop_result.tool_calls_log,
            total_steps=loop_result.total_steps,
            total_tokens=loop_result.total_tokens,
            provider=loop_result.provider,
            model=loop_result.model,
            error=loop_result.error,
        )
