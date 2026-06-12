# -*- coding: utf-8 -*-
"""Factory for CS item chat Agent (ReAct + tools), aligned with stock 问股 mode."""

from __future__ import annotations

import logging
from typing import List, Optional

from src.agent.config_utils import coerce_config_int
from src.config import AGENT_MAX_STEPS_DEFAULT

logger = logging.getLogger(__name__)

_CS_TOOL_REGISTRY = None


def get_cs_tool_registry():
    global _CS_TOOL_REGISTRY
    if _CS_TOOL_REGISTRY is not None:
        return _CS_TOOL_REGISTRY

    from src.agent.tools.registry import ToolRegistry
    from src.agent.tools.cs_tools import ALL_CS_TOOLS

    registry = ToolRegistry()
    for tool_def in ALL_CS_TOOLS:
        registry.register(tool_def)

    _CS_TOOL_REGISTRY = registry
    logger.info("[CSAgentFactory] ToolRegistry cached (%d tools)", len(registry._tools))
    return _CS_TOOL_REGISTRY


def build_cs_agent_executor(config=None, skills: Optional[List[str]] = None):
    """Build CSAgentExecutor with CS-only tools and CS skill prompts."""
    if config is None:
        from src.config import get_config

        config = get_config()

    from src.agent.cs_executor import CSAgentExecutor
    from src.agent.llm_adapter import LLMToolAdapter
    from src.services.cs_skill_prompt import (
        CS_SKILL_DATA_MAPPING,
        CS_TRADING_BASELINE_ZH,
        resolve_cs_skill_prompt,
    )

    skill_state = resolve_cs_skill_prompt(skills)
    llm_adapter = LLMToolAdapter(config)

    return CSAgentExecutor(
        tool_registry=get_cs_tool_registry(),
        llm_adapter=llm_adapter,
        skill_instructions=skill_state.skill_instructions,
        data_mapping=CS_SKILL_DATA_MAPPING,
        baseline=CS_TRADING_BASELINE_ZH,
        max_steps=coerce_config_int(
            getattr(config, "agent_max_steps", AGENT_MAX_STEPS_DEFAULT),
            AGENT_MAX_STEPS_DEFAULT,
            field_name="agent_max_steps",
        ),
        timeout_seconds=coerce_config_int(
            getattr(config, "agent_orchestrator_timeout_s", 0),
            0,
            field_name="agent_orchestrator_timeout_s",
        ),
    )
