# -*- coding: utf-8 -*-
"""Extract CS inventory rows from app screenshots via Vision LLM."""

from __future__ import annotations

import base64
import json
import logging
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from src.services.cs_holdings_dedup import reconcile_item_name_and_wear
from src.services.image_stock_extractor import (
    ALLOWED_MIME,
    MAX_SIZE_BYTES,
    _call_litellm_vision,
    _get_api_keys_for_model,
    _resolve_vision_model,
    _verify_image_magic_bytes,
    format_vision_api_error,
)

logger = logging.getLogger(__name__)

CS_HOLDINGS_EXTRACT_PROMPT = """请分析这张 CS2（Counter-Strike 2）饰品库存/持仓 App 截图，提取汇总数据与每一行饰品。

输出要求：仅返回一个 JSON 对象，不要 markdown、不要解释。

JSON 结构：
{
  "summary": {
    "total_market_value": 数字或null,
    "total_pnl": 数字或null,
    "total_cost": 数字或null,
    "item_count": 整数或null
  },
  "items": [
    {
      "item_name": "完整中文饰品名（含武器+皮肤+磨损，如 AK-47 | 野荷 (崭新出厂)）",
      "weapon_name": "武器名（可含★）",
      "skin_name": "皮肤名",
      "wear": "崭新出厂|略有磨损|久经沙场|破损不堪|战痕累累 或英文磨损",
      "float_value": 数字或null,
      "market_price": 数字或null,
      "purchase_price": 数字或null,
      "pnl": 数字或null,
      "confidence": "high|medium|low"
    }
  ]
}

规则：
- 价格单位为元（¥），只填数字，不要货币符号。
- 若截图有「市场价」「购入价」「盈亏」列，逐行提取；盈亏可为负数。
- 汇总区若有「市场价」「总盈亏」「购入总价」「件数」，填入 summary。
- 看不清的数字填 null，confidence 设为 low。
- 未找到任何饰品时 items 返回 []。"""

_VALID_CONFIDENCE = frozenset({"high", "medium", "low"})
_VISION_MAX_ATTEMPTS = 2


def _parse_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    for start in ("```json", "```"):
        if cleaned.startswith(start):
            cleaned = cleaned[len(start) :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    payload = match.group(0) if match else cleaned
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Vision 返回的不是 JSON 对象")
    return data


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, str):
            value = value.replace("¥", "").replace(",", "").strip()
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    conf = str(raw.get("confidence") or "medium").lower()
    if conf not in _VALID_CONFIDENCE:
        conf = "medium"
    weapon = str(raw.get("weapon_name") or "").strip()
    skin = str(raw.get("skin_name") or "").strip()
    wear = str(raw.get("wear") or "").strip()
    item_name = str(raw.get("item_name") or "").strip()
    if not item_name and weapon:
        parts = [weapon]
        if skin:
            parts.append(skin)
        item_name = " | ".join(parts)
        if wear:
            item_name = f"{item_name} ({wear})"
    item_name, wear = reconcile_item_name_and_wear(item_name, wear)
    return {
        "item_name": item_name,
        "weapon_name": weapon,
        "skin_name": skin,
        "wear": wear,
        "float_value": _to_float(raw.get("float_value")),
        "market_price": _to_float(raw.get("market_price")),
        "purchase_price": _to_float(raw.get("purchase_price")),
        "pnl": _to_float(raw.get("pnl")),
        "confidence": conf,
    }


def _call_vision_for_holdings(image_b64: str, mime_type: str) -> str:
    from src.config import get_config

    model = _resolve_vision_model()
    keys = _get_api_keys_for_model(model, get_config())
    last_error: Optional[Exception] = None
    for attempt in range(_VISION_MAX_ATTEMPTS):
        try:
            key = random.choice(keys) if keys else None
            return _call_litellm_vision(
                image_b64,
                mime_type,
                api_key=key,
                prompt=CS_HOLDINGS_EXTRACT_PROMPT,
            )
        except Exception as exc:
            last_error = exc
            if attempt < _VISION_MAX_ATTEMPTS - 1:
                delay = 2 ** attempt
                logger.warning(
                    "[CSHoldingsVision] attempt %s/%s failed, retry in %ss: %s",
                    attempt + 1,
                    _VISION_MAX_ATTEMPTS,
                    delay,
                    exc,
                )
                time.sleep(delay)
    raise ValueError(format_vision_api_error(last_error or RuntimeError("Vision API failed"))) from last_error


def extract_cs_holdings_from_image(
    image_bytes: bytes,
    mime_type: str,
) -> Tuple[Dict[str, Any], str]:
    if mime_type not in ALLOWED_MIME:
        raise ValueError(f"不支持的图片类型: {mime_type}")
    if len(image_bytes) > MAX_SIZE_BYTES:
        raise ValueError(f"图片超过 {MAX_SIZE_BYTES // (1024 * 1024)}MB 限制")
    _verify_image_magic_bytes(image_bytes, mime_type)

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    raw_text = _call_vision_for_holdings(image_b64, mime_type)
    data = _parse_json_object(raw_text)

    summary_raw = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    summary = {
        "total_market_value": _to_float(summary_raw.get("total_market_value")),
        "total_pnl": _to_float(summary_raw.get("total_pnl")),
        "total_cost": _to_float(summary_raw.get("total_cost")),
        "item_count": int(summary_raw["item_count"]) if str(summary_raw.get("item_count", "")).isdigit() else None,
    }

    items: List[Dict[str, Any]] = []
    for row in data.get("items") or []:
        if isinstance(row, dict) and (row.get("item_name") or row.get("weapon_name")):
            items.append(_normalize_item(row))

    return {"summary": summary, "items": items}, raw_text
