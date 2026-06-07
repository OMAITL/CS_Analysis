# -*- coding: utf-8 -*-
"""CS item analysis service for API layer."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from market_provider.csqaq.item_analysis import run_cs_item_analysis
from src.services.cs_event_intel_service import fetch_cs_event_intel


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


_TREND_FLOAT_KEYS = (
    "trend_strength",
    "ma5",
    "ma10",
    "ma20",
    "ma60",
    "current_price",
    "bias_ma5",
    "volume_ratio_5d",
    "macd_dif",
    "macd_dea",
    "rsi_12",
)


def _serialize_trend(raw: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "code": str(raw.get("code") or ""),
        "trend_status": str(raw.get("trend_status") or ""),
        "ma_alignment": str(raw.get("ma_alignment") or ""),
        "volume_status": str(raw.get("volume_status") or ""),
        "buy_signal": str(raw.get("buy_signal") or ""),
        "macd_status": str(raw.get("macd_status") or ""),
        "rsi_status": str(raw.get("rsi_status") or ""),
        "signal_reasons": list(raw.get("signal_reasons") or []),
        "risk_factors": list(raw.get("risk_factors") or []),
    }
    for key in _TREND_FLOAT_KEYS:
        out[key] = _safe_float(raw.get(key), 0.0) or 0.0
    score = raw.get("signal_score")
    try:
        out["signal_score"] = int(score) if score is not None else 0
    except (TypeError, ValueError):
        out["signal_score"] = 0
    return out


def _serialize_snapshot(raw: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in (
        "name",
        "market_hash_name",
        "buff_sell_price",
        "yyyp_sell_price",
        "steam_sell_price",
        "updated_at",
    ):
        if raw.get(key) is not None:
            out[key] = raw[key]
    for key in ("buff_sell_num", "yyyp_sell_num"):
        value = raw.get(key)
        if value is None:
            continue
        try:
            out[key] = int(value)
        except (TypeError, ValueError):
            pass
    turnover = _safe_float(raw.get("turnover_number"))
    if turnover is not None:
        out["turnover_number"] = turnover
    return out


def _serialize_ohlcv_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for rec in rows:
        close = _safe_float(rec.get("close"))
        if close is None:
            continue
        open_ = _safe_float(rec.get("open"), close)
        high = _safe_float(rec.get("high"), close)
        low = _safe_float(rec.get("low"), close)
        serialized.append(
            {
                "date": str(rec.get("date")),
                "open": open_ if open_ is not None else close,
                "high": high if high is not None else close,
                "low": low if low is not None else close,
                "close": close,
                "volume": _safe_float(rec.get("volume"), 0.0) or 0.0,
                "amount": _safe_float(rec.get("amount")),
                "change_percent": _safe_float(rec.get("pct_chg") or rec.get("change_percent")),
            }
        )
    return serialized


class CSItemService:
    """Run fused CS item analysis and optional LLM report for Web/API."""

    def analyze_item(
        self,
        *,
        good_id: Optional[int] = None,
        item: Optional[str] = None,
        platform: Optional[str] = None,
        period: int = 365,
        prefer_crawl: bool = True,
        refresh_crawl: bool = False,
        refresh_today: bool = True,
        kline_pages: int = 5,
        include_report: bool = True,
        skills: Optional[List[str]] = None,
        fallback_name: str = "",
        fallback_mhn: str = "",
    ) -> Dict[str, Any]:
        from src.services.cs_skill_prompt import normalize_cs_skill_ids
        active_skills = normalize_cs_skill_ids(skills)
        ctx = run_cs_item_analysis(
            good_id=good_id,
            item_query=item,
            platform=platform,
            period=period,
            prefer_crawl=prefer_crawl,
            refresh_crawl=refresh_crawl,
            refresh_today=refresh_today,
            kline_pages=kline_pages,
            fallback_name=fallback_name,
            fallback_mhn=fallback_mhn,
        )

        event_context, event_items = fetch_cs_event_intel(
            ctx.good_id,
            ctx.item_name,
            ctx.market_hash_name,
        )
        ctx.event_context = event_context
        ctx.event_intel = event_items

        report_markdown = ""
        report_source = "none"
        llm_result = None
        if include_report:
            try:
                from src.services.cs_analysis_report import run_cs_item_llm_analysis

                report_markdown, report_source, _, llm_result = run_cs_item_llm_analysis(
                    ctx,
                    skills=active_skills,
                )
            except Exception:
                report_markdown, report_source = "", "none"

        from src.services.cs_analysis_report import build_cs_report_payload

        report_payload = build_cs_report_payload(ctx, llm_result)

        snapshot = _serialize_snapshot(ctx.snapshot)

        meta_payload = ctx.meta.model_dump(mode="json")
        platform_raw = meta_payload.get("platform")
        if isinstance(platform_raw, int):
            from market_provider.csqaq.schemas import CSQAQPlatform

            try:
                meta_payload["platform"] = CSQAQPlatform(platform_raw).name.lower()
            except ValueError:
                meta_payload["platform"] = str(platform_raw)

        return {
            "good_id": ctx.good_id,
            "item_name": ctx.item_name,
            "market_hash_name": ctx.market_hash_name,
            "platform": ctx.platform,
            "snapshot": snapshot,
            "meta": meta_payload,
            "trend": _serialize_trend(ctx.trend.to_dict()),
            "ohlcv": _serialize_ohlcv_rows(ctx.ohlcv_rows),
            "report_markdown": report_markdown,
            "report_source": report_source,
            "report": report_payload,
            "event_intel": event_items,
            "event_context": event_context,
            "active_skills": active_skills,
        }

    def search_items(
        self,
        search: str,
        *,
        page_index: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Search CS items: local catalog first, CSQAQ fallback."""
        term = (search or "").strip()
        if not term:
            raise ValueError("search is required")
        from src.services.cs_item_catalog_service import CSItemCatalogService

        payload = CSItemCatalogService().search_hybrid(
            term,
            page_index=page_index,
            page_size=page_size,
        )
        payload.pop("source", None)
        return payload

    def search_items_remote(
        self,
        search: str,
        *,
        page_index: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Fuzzy search CS items via CSQAQ get_good_id (CN/EN names)."""
        term = (search or "").strip()
        if not term:
            raise ValueError("search is required")
        from market_provider.csqaq.client import CSQAQClient

        client = CSQAQClient()
        result = client.search_goods(
            term,
            page_index=max(1, int(page_index)),
            page_size=max(1, min(int(page_size), 50)),
        )
        items = [
            {
                "good_id": int(entry.id),
                "name": str(entry.name),
                "market_hash_name": str(entry.market_hash_name),
            }
            for entry in result.items
        ]
        return {
            "items": items,
            "page_index": int(result.page_index),
            "page_size": int(result.page_size),
            "total": int(result.total),
        }
