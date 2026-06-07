#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trace CS chat pipeline step-by-step for one user message."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent.conversation import conversation_manager
from src.services.cs_chat_pipeline import (
    build_narrator_context_block,
    run_cs_chat_pipeline,
    try_build_resolution_failure_reply,
)
from src.services.cs_entity_resolver import detect_intent, resolve_entities, _extract_item_query_candidates


def _short(obj, limit: int = 800) -> str:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if len(text) > limit:
        return text[:limit] + "\n... (truncated)"
    return text


def trace(message: str) -> None:
    sid = "cs_trace_demo_session"
    conversation_manager.clear(sid)

    print("=" * 60)
    print("用户消息:", message)
    print("=" * 60)

    print("\n【步骤 1】程序从消息里提取饰品候选词")
    cands = _extract_item_query_candidates(message)
    for i, c in enumerate(cands[:6], 1):
        print(f"  候选 {i}: {c}")

    print("\n【步骤 2】程序判断用户意图（不是 LLM）")
    intent = detect_intent(message)
    print(f"  intent = {intent}")

    print("\n【步骤 3】程序解析 good_id（本地库 → CSQAQ → 浏览器兜底）")
    entity = resolve_entities(message)
    print(f"  good_id      = {entity.good_id}")
    print(f"  item_name    = {entity.item_name}")
    print(f"  item_query   = {entity.item_query}")
    print(f"  source       = {entity.source}")
    print(f"  confidence   = {entity.confidence}")
    if entity.catalog_candidates:
        print("  top candidates:")
        for row in entity.catalog_candidates[:3]:
            print(f"    - id={row.get('good_id')} name={row.get('name')} score={row.get('score')}")

    print("\n【步骤 4】跑完整管线（认饰品 → 拉数据 → Skill 分析）")
    progress: list[str] = []

    def on_progress(ev: dict) -> None:
        msg = str(ev.get("message") or "").strip()
        if msg:
            progress.append(msg)

    pipeline = run_cs_chat_pipeline(
        session_id=sid,
        message=message,
        request_context=None,
        progress_callback=on_progress,
    )
    for i, msg in enumerate(progress, 1):
        print(f"  进度 {i}: {msg}")
    print(f"  scope = {pipeline.scope}")

    failure = try_build_resolution_failure_reply(pipeline)
    if failure:
        print("\n【步骤 5】解析/拉数失败 → 直接返回固定文案（不调 LLM）")
        print(failure[:600])
        return

    bundle = pipeline.item_bundle
    skills = pipeline.skill_result

    print("\n【步骤 5】数据拉取结果（ItemDataProvider）")
    if bundle is None:
        print("  （无单品数据包 — 未进入 single_item 或 good_id 为空）")
    else:
        print(f"  good_id        = {bundle.good_id}")
        print(f"  name           = {(bundle.item_info or {}).get('name')}")
        print(f"  error          = {bundle.error}")
        print(f"  K线条数        = {len(bundle.price_history or [])}")
        print(f"  data_quality   = {(bundle.meta or {}).get('data_quality')}")
        print(f"  crawl_backfill = {(bundle.meta or {}).get('crawl_backfill')}")
        print(f"  crawl_status   = {(bundle.meta or {}).get('crawl_backfill_status')}")
        trend = bundle.trend or {}
        if trend:
            print(f"  当前价         = {trend.get('current_price')}")
            print(f"  信号分         = {trend.get('signal_score')}")
            print(f"  买入信号       = {trend.get('buy_signal')}")
            print(f"  RSI            = {trend.get('rsi_12')}")
            print(f"  乖离MA5        = {trend.get('bias_ma5')}%")
            print(f"  风险因素       = {(trend.get('risk_factors') or [])[:3]}")

    print("\n【步骤 6】程序 Skill 分析结果（CSSkillEngine，不是 LLM）")
    if skills is None:
        print("  （未运行 Skill）")
    else:
        print(f"  active_skills = {skills.active_skills}")
        if skills.trend:
            print(f"  trend.summary = {(skills.trend or {}).get('summary')}")
        if skills.risk:
            print(f"  risk.level    = {(skills.risk or {}).get('risk_level')} score={(skills.risk or {}).get('score')}")
        if skills.manipulation:
            print(
                f"  manipulation  = score={(skills.manipulation or {}).get('score')} "
                f"prob={(skills.manipulation or {}).get('probability')}"
            )

    print("\n【步骤 7】注入 LLM 的 JSON 摘要（LLM 只能解释这份数据）")
    block = build_narrator_context_block(pipeline)
    # extract mode line
    mode = (pipeline.narrator_payload or {}).get("mode")
    print(f"  mode = {mode}")
    print(_short(pipeline.narrator_payload, limit=1200))

    print("\n【步骤 8】LLM 角色")
    print("  模型在此步才介入：读取上面 JSON + 用户问题 → 写自然语言回答")
    print("  LLM 不会再次查库、不会跑首页完整报告、没有 tool calling")


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "M4A1 闪回现在很高位，适合卖吗？还是我继续持有可以有更多钱"
    trace(msg)
