# -*- coding: utf-8 -*-
"""Multi-turn CS item Q&A — ReAct Agent mode (aligned with stock 问股)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence

from src.config import get_config, get_effective_agent_primary_model

logger = logging.getLogger(__name__)

CS_SESSION_PREFIX = "cs_"


@dataclass
class CSChatResult:
    success: bool
    content: str
    session_id: str
    error: Optional[str] = None


def normalize_cs_session_id(session_id: Optional[str]) -> str:
    raw = (session_id or "").strip()
    if not raw:
        return f"{CS_SESSION_PREFIX}{uuid.uuid4()}"
    if raw.startswith(CS_SESSION_PREFIX):
        return raw
    return f"{CS_SESSION_PREFIX}{raw}"


class CSChatService:
    """CS chat backed by CSAgentExecutor (tool-calling ReAct loop)."""

    def chat(
        self,
        *,
        message: str,
        session_id: Optional[str] = None,
        skills: Optional[Sequence[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> CSChatResult:
        text = (message or "").strip()
        sid = normalize_cs_session_id(session_id)
        if not text:
            return CSChatResult(success=False, content="", session_id=sid, error="message is required")

        config = get_config()
        primary_model = get_effective_agent_primary_model(config) or (getattr(config, "litellm_model", "") or "").strip()
        if not primary_model:
            return CSChatResult(
                success=False,
                content="",
                session_id=sid,
                error="未配置可用的 LLM 模型，请在系统设置或 .env 中配置 LITELLM_MODEL / LLM 渠道",
            )

        try:
            from src.agent.cs_factory import build_cs_agent_executor

            executor = build_cs_agent_executor(config, skills=list(skills) if skills else None)
            result = executor.chat(
                message=text,
                session_id=sid,
                progress_callback=progress_callback,
                context=context,
            )
            return CSChatResult(
                success=result.success,
                content=result.content or "",
                session_id=sid,
                error=result.error,
            )
        except Exception as exc:
            logger.error("CS chat agent failed: %s", exc, exc_info=True)
            return CSChatResult(success=False, content="", session_id=sid, error=str(exc))
