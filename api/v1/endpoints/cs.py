# -*- coding: utf-8 -*-
"""CS item analysis endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Optional

import requests
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from market_provider.csqaq.client import CSQAQAPIError

from api.v1.schemas.common import ErrorResponse
from api.v1.schemas.cs import (
    CSChatRequest,
    CSChatResponse,
    CSChatSessionMessagesResponse,
    CSChatSessionsResponse,
    CSHoldingBulkCreateRequest,
    CSHoldingCreateRequest,
    CSHoldingItem,
    CSHoldingsExtractResponse,
    CSHoldingsImportCommitRequest,
    CSHoldingsImportCommitResponse,
    CSHoldingsImportPreviewRequest,
    CSHoldingsImportPreviewResponse,
    CSHoldingsImportUpdateRequest,
    CSHoldingsRiskResponse,
    CSHoldingsSnapshotResponse,
    CSHoldingUpdateRequest,
    CSItemAnalyzeRequest,
    CSItemAnalyzeResponse,
    CSItemCatalogStatusResponse,
    CSItemCatalogSyncResponse,
    CSItemSearchResponse,
)
from src.services.cs_chat_service import CSChatService, CS_SESSION_PREFIX, normalize_cs_session_id

CS_TOOL_DISPLAY_NAMES: Dict[str, str] = {
    "search_cs_item": "检索饰品 good_id",
    "analyze_cs_item": "拉取 K 线与技术指标",
    "search_cs_item_intel": "搜索饰品事件情报",
    "get_cs_market_overview": "获取市场指数/扫描",
    "get_cs_portfolio_snapshot": "读取持仓快照",
}
from src.services.cs_holdings_service import CSHoldingsService
from src.services.cs_holdings_import_service import CSHoldingsImportService
from src.services.cs_holdings_risk_service import CSHoldingsRiskService
from src.services.cs_item_catalog_service import CSItemCatalogService
from src.services.cs_item_service import CSItemService
from src.services.cs_skill_prompt import list_cs_skills

logger = logging.getLogger(__name__)


def _raise_vision_http_error(exc: Exception) -> None:
    from src.services.image_stock_extractor import format_vision_api_error

    message = str(exc) if isinstance(exc, ValueError) else format_vision_api_error(exc)
    err_lower = message.lower()
    if any(token in err_lower for token in ("timeout", "timed out", "超时", "无法连接", "10060")):
        raise HTTPException(
            status_code=504,
            detail={"error": "vision_timeout", "message": message},
        ) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=400,
            detail={"error": "extract_failed", "message": message},
        ) from exc
    raise HTTPException(
        status_code=502,
        detail={"error": "vision_failed", "message": message},
    ) from exc

router = APIRouter()

_CSQAQ_AUTH_HINT = (
    "CSQAQ 返回 401：请检查 .env 中 CSQAQ_API_TOKEN 是否正确，"
    "并在 CSQAQ 用户中心将本机公网 IP 加入白名单后重启 uvicorn。"
)


def _raise_cs_upstream_error(exc: Exception) -> None:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        if exc.response.status_code == 401:
            raise HTTPException(
                status_code=502,
                detail={"error": "csqaq_unauthorized", "message": _CSQAQ_AUTH_HINT},
            ) from exc
        raise HTTPException(
            status_code=502,
            detail={
                "error": "csqaq_upstream_error",
                "message": f"CSQAQ 请求失败（HTTP {exc.response.status_code}）",
            },
        ) from exc
    if isinstance(exc, CSQAQAPIError) and exc.code == 401:
        raise HTTPException(
            status_code=502,
            detail={"error": "csqaq_unauthorized", "message": _CSQAQ_AUTH_HINT},
        ) from exc
    if isinstance(exc, CSQAQAPIError):
        raise HTTPException(
            status_code=502,
            detail={
                "error": "csqaq_upstream_error",
                "message": str(exc) or "CSQAQ API error",
            },
        ) from exc


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
        "Search CS items by name. Uses local CSQAQ catalog mirror when available; "
        "falls back to CSQAQ get_good_id and upserts results into the local cache."
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
    except HTTPException:
        raise
    except (requests.HTTPError, CSQAQAPIError) as exc:
        logger.error("CS item search upstream failed: %s", exc, exc_info=True)
        _raise_cs_upstream_error(exc)
    except Exception as exc:
        logger.error("CS item search failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"CS item search failed: {exc}"},
        ) from exc


@router.get(
    "/items/catalog/status",
    response_model=CSItemCatalogStatusResponse,
    summary="CS item catalog sync status",
)
def cs_item_catalog_status() -> CSItemCatalogStatusResponse:
    return CSItemCatalogStatusResponse(**CSItemCatalogService().get_status())


@router.post(
    "/items/catalog/sync",
    response_model=CSItemCatalogSyncResponse,
    summary="Sync CS item catalog from CSQAQ",
    description=(
        "Pull paginated item list via CSQAQ get_page_list into local SQLite. "
        "Use mode=full for baseline sync; mode=incremental for tail/new-item updates."
    ),
)
def cs_item_catalog_sync(
    mode: str = "incremental",
    resume: bool = False,
    max_pages: Optional[int] = None,
) -> CSItemCatalogSyncResponse:
    normalized = (mode or "incremental").strip().lower()
    if normalized not in {"full", "incremental"}:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_params", "message": "mode must be full or incremental"},
        )
    try:
        payload = CSItemCatalogService().sync(
            normalized,
            resume=resume,
            max_pages=max_pages,
        )
        return CSItemCatalogSyncResponse(**payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_params", "message": str(exc)},
        ) from exc
    except HTTPException:
        raise
    except (requests.HTTPError, CSQAQAPIError) as exc:
        logger.error("CS catalog sync upstream failed: %s", exc, exc_info=True)
        _raise_cs_upstream_error(exc)
    except Exception as exc:
        logger.error("CS catalog sync failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"CS catalog sync failed: {exc}"},
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
    except HTTPException:
        raise
    except (requests.HTTPError, CSQAQAPIError) as exc:
        logger.error("CS item analyze upstream failed: %s", exc, exc_info=True)
        _raise_cs_upstream_error(exc)
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


@router.post(
    "/chat",
    response_model=CSChatResponse,
    summary="CS item multi-turn chat",
)
async def cs_chat(request: CSChatRequest) -> CSChatResponse:
    session_id = normalize_cs_session_id(request.session_id)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: CSChatService().chat(
            message=request.message,
            session_id=session_id,
            skills=request.skills,
            context=request.context,
        ),
    )
    return CSChatResponse(
        success=result.success,
        content=result.content,
        session_id=result.session_id,
        error=result.error,
    )


@router.post("/chat/stream")
async def cs_chat_stream(request: CSChatRequest):
    """SSE stream compatible with frontend agent chat store (generating + done)."""
    session_id = normalize_cs_session_id(request.session_id)
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def progress_callback(event: dict):
        if event.get("type") in ("tool_start", "tool_done"):
            tool = event.get("tool", "")
            event["display_name"] = CS_TOOL_DISPLAY_NAMES.get(tool, tool)
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    def run_sync():
        try:
            result = CSChatService().chat(
                message=request.message,
                session_id=session_id,
                skills=request.skills,
                context=request.context,
                progress_callback=progress_callback,
            )
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "done",
                    "success": result.success,
                    "content": result.content,
                    "error": result.error,
                    "session_id": result.session_id,
                    "linked_item": result.linked_item,
                }),
                loop,
            )
        except Exception as exc:
            logger.error("CS chat stream error: %s", exc, exc_info=True)
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": "error", "message": str(exc)}),
                loop,
            )

    async def event_generator():
        fut = loop.run_in_executor(None, run_sync)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=180.0)
                except asyncio.TimeoutError:
                    yield "data: " + json.dumps({"type": "error", "message": "回答超时"}, ensure_ascii=False) + "\n\n"
                    break
                yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
                if event.get("type") in ("done", "error"):
                    break
        finally:
            try:
                await asyncio.wait_for(fut, timeout=5.0)
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/chat/sessions", response_model=CSChatSessionsResponse)
async def list_cs_chat_sessions(limit: int = 50) -> CSChatSessionsResponse:
    from src.storage import get_db

    sessions = get_db().get_chat_sessions(limit=limit, session_prefix=CS_SESSION_PREFIX)
    return CSChatSessionsResponse(sessions=sessions)


@router.get("/chat/sessions/{session_id}", response_model=CSChatSessionMessagesResponse)
async def get_cs_chat_session_messages(session_id: str, limit: int = 100) -> CSChatSessionMessagesResponse:
    sid = normalize_cs_session_id(session_id)
    from src.storage import get_db
    from src.services.cs_chat_session_binding import resolve_session_binding

    messages = get_db().get_conversation_messages(sid, limit=limit)
    linked_item = resolve_session_binding(sid, messages)
    return CSChatSessionMessagesResponse(session_id=sid, messages=messages, linked_item=linked_item)


@router.delete("/chat/sessions/{session_id}/item")
async def clear_cs_chat_session_item(session_id: str) -> dict:
    sid = normalize_cs_session_id(session_id)
    from src.services.cs_chat_session_binding import delete_session_binding
    from src.services.cs_chat_session import clear_current_item

    delete_session_binding(sid)
    clear_current_item(sid)
    return {"session_id": sid, "cleared": True}


@router.delete("/chat/sessions/{session_id}")
async def delete_cs_chat_session(session_id: str) -> dict:
    sid = normalize_cs_session_id(session_id)
    from src.storage import get_db
    from src.services.cs_chat_session_binding import delete_session_binding

    count = get_db().delete_conversation_session(sid)
    delete_session_binding(sid)
    from src.agent.conversation import conversation_manager

    conversation_manager.clear(sid)
    return {"deleted": count, "session_id": sid}


@router.get(
    "/holdings/snapshot",
    response_model=CSHoldingsSnapshotResponse,
    summary="CS holdings snapshot with P&L",
)
def cs_holdings_snapshot(
    refresh_prices: bool = True,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    platform: Optional[str] = None,
    sort: str = "updated_at",
) -> CSHoldingsSnapshotResponse:
    payload = CSHoldingsService().get_snapshot(
        refresh_prices=refresh_prices,
        page=page,
        page_size=page_size,
        platform=platform,
        sort=sort,
    )
    return CSHoldingsSnapshotResponse(**payload)


@router.get(
    "/holdings/risk",
    response_model=CSHoldingsRiskResponse,
    summary="CS holdings risk report",
)
def cs_holdings_risk(
    refresh_prices: bool = True,
    platform: Optional[str] = None,
) -> CSHoldingsRiskResponse:
    data = CSHoldingsRiskService().get_risk_report(
        platform=platform,
        refresh_prices=refresh_prices,
    )
    return CSHoldingsRiskResponse(**data)


@router.post(
    "/holdings",
    response_model=CSHoldingItem,
    summary="Create CS holding (manual entry)",
)
def create_cs_holding(request: CSHoldingCreateRequest) -> CSHoldingItem:
    try:
        row = CSHoldingsService().create_holding(**request.model_dump())
        return CSHoldingItem(**row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_params", "message": str(exc)}) from exc


@router.post(
    "/holdings/bulk",
    response_model=CSHoldingsSnapshotResponse,
    summary="Bulk create CS holdings",
)
def bulk_create_cs_holdings(request: CSHoldingBulkCreateRequest) -> CSHoldingsSnapshotResponse:
    CSHoldingsService().bulk_create([item.model_dump() for item in request.items])
    payload = CSHoldingsService().get_snapshot(refresh_prices=True)
    return CSHoldingsSnapshotResponse(**payload)


@router.put(
    "/holdings/{holding_id}",
    response_model=CSHoldingItem,
    summary="Update CS holding",
)
def update_cs_holding(holding_id: int, request: CSHoldingUpdateRequest) -> CSHoldingItem:
    try:
        row = CSHoldingsService().update_holding(
            holding_id,
            **request.model_dump(exclude_unset=True),
        )
        return CSHoldingItem(**row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": str(exc)}) from exc


@router.delete("/holdings/{holding_id}")
def delete_cs_holding(holding_id: int) -> dict:
    try:
        CSHoldingsService().delete_holding(holding_id)
        return {"success": True}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": str(exc)}) from exc


@router.post(
    "/holdings/extract-from-image",
    response_model=CSHoldingsExtractResponse,
    summary="Extract CS holdings from inventory app screenshot",
)
async def extract_cs_holdings_from_image(file: UploadFile = File(...)) -> CSHoldingsExtractResponse:
    mime = (file.content_type or "").split(";")[0].strip().lower()
    if mime not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise HTTPException(status_code=400, detail={"error": "invalid_mime", "message": f"不支持的图片类型: {mime}"})
    data = await file.read()
    try:
        payload = CSHoldingsService().extract_from_image(data, mime)
        return CSHoldingsExtractResponse(**payload)
    except ValueError as exc:
        _raise_vision_http_error(exc)
    except Exception as exc:
        logger.error("CS holdings image extract failed: %s", exc, exc_info=True)
        _raise_vision_http_error(exc)


@router.post(
    "/holdings/rematch-good-ids",
    summary="Backfill missing good_id for existing CS holdings",
)
def rematch_cs_holdings_good_ids() -> dict:
    summary = CSHoldingsService().rematch_missing_good_ids()
    return {"success": True, **summary}


@router.post(
    "/holdings/import/preview",
    response_model=CSHoldingsImportPreviewResponse,
    summary="Preview CS holdings import (manual/csv items)",
)
def preview_cs_holdings_import(request: CSHoldingsImportPreviewRequest) -> CSHoldingsImportPreviewResponse:
    try:
        payload = CSHoldingsImportService().preview_from_items(
            source=request.source,
            items=[item.model_dump() for item in request.items],
        )
        return CSHoldingsImportPreviewResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_params", "message": str(exc)}) from exc


@router.post(
    "/holdings/import/preview/image",
    response_model=CSHoldingsImportPreviewResponse,
    summary="Preview CS holdings import from inventory screenshot",
)
async def preview_cs_holdings_import_image(file: UploadFile = File(...)) -> CSHoldingsImportPreviewResponse:
    mime = (file.content_type or "").split(";")[0].strip().lower()
    if mime not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise HTTPException(status_code=400, detail={"error": "invalid_mime", "message": f"不支持的图片类型: {mime}"})
    data = await file.read()
    try:
        payload = CSHoldingsImportService().preview_from_image(data, mime)
        return CSHoldingsImportPreviewResponse(**payload)
    except ValueError as exc:
        _raise_vision_http_error(exc)
    except Exception as exc:
        logger.error("CS holdings import preview image failed: %s", exc, exc_info=True)
        _raise_vision_http_error(exc)


@router.post(
    "/holdings/import/update",
    response_model=CSHoldingsImportPreviewResponse,
    summary="Update import preview drafts and optionally rematch",
)
def update_cs_holdings_import_preview(request: CSHoldingsImportUpdateRequest) -> CSHoldingsImportPreviewResponse:
    try:
        payload = CSHoldingsImportService().update_session_drafts(
            request.session_id,
            [draft.model_dump() for draft in request.drafts],
            rematch=request.rematch,
        )
        return CSHoldingsImportPreviewResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "message": str(exc)}) from exc


@router.post(
    "/holdings/import/commit",
    response_model=CSHoldingsImportCommitResponse,
    summary="Commit import preview session to holdings",
)
def commit_cs_holdings_import(request: CSHoldingsImportCommitRequest) -> CSHoldingsImportCommitResponse:
    try:
        payload = CSHoldingsImportService().commit_session(
            request.session_id,
            draft_ids=request.draft_ids,
            skip_duplicates=request.skip_duplicates,
        )
        return CSHoldingsImportCommitResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "commit_failed", "message": str(exc)}) from exc
