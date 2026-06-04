# -*- coding: utf-8 -*-
"""CS item analysis endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.v1.schemas.common import ErrorResponse
from api.v1.schemas.cs import (
    CSItemAnalyzeRequest,
    CSItemAnalyzeResponse,
    CSItemSearchResponse,
)
from src.services.cs_item_service import CSItemService
from src.services.cs_skill_prompt import list_cs_skills

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/items/search",
    response_model=CSItemSearchResponse,
    responses={
        200: {"description": "CS item search results"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
    summary="Search CS items by name",
    description=(
        "Fuzzy search CSQAQ good_id by Chinese or English item name "
        "(CSQAQ POST /api/v1/info/get_good_id). Use when knife type or skin "
        "name matches many variants."
    ),
)
def search_cs_items(
    search: str,
    page_index: int = 1,
    page_size: int = 20,
) -> CSItemSearchResponse:
    if not (search or "").strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_params", "message": "search is required"},
        )
    try:
        payload = CSItemService().search_items(
            search.strip(),
            page_index=page_index,
            page_size=page_size,
        )
        return CSItemSearchResponse(**payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_params", "message": str(exc)},
        ) from exc
    except Exception as exc:
        logger.error("CS item search failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"CS item search failed: {exc}"},
        ) from exc


@router.post(
    "/items/analyze",
    response_model=CSItemAnalyzeResponse,
    responses={
        200: {"description": "CS item analysis completed"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
    summary="Analyze CS item",
    description="Fuse API + crawler OHLCV, run trend analysis, optional LLM Markdown report",
)
def analyze_cs_item(request: CSItemAnalyzeRequest) -> CSItemAnalyzeResponse:
    if not request.good_id and not (request.item or "").strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_params", "message": "good_id or item is required"},
        )
    try:
        payload = CSItemService().analyze_item(
            good_id=request.good_id,
            item=request.item,
            platform=request.platform,
            period=request.period,
            prefer_crawl=request.prefer_crawl,
            refresh_crawl=request.refresh_crawl,
            refresh_today=request.refresh_today,
            kline_pages=request.kline_pages,
            include_report=request.include_report,
            skills=request.skills,
        )
        return CSItemAnalyzeResponse(**payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_params", "message": str(exc)},
        ) from exc
    except Exception as exc:
        logger.error("CS item analyze failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"CS item analyze failed: {exc}"},
        ) from exc


@router.get(
    "/items/skills",
    summary="List CS-compatible trading skills",
)
def list_cs_item_skills() -> dict:
    return {"skills": list_cs_skills(), "default": ["bull_trend"]}


@router.get(
    "/items/health",
    summary="CS module health",
)
def cs_health() -> dict:
    token_set = bool(__import__("os").getenv("CSQAQ_API_TOKEN", "").strip())
    return {"status": "ok", "csqaq_token_set": token_set}
