# -*- coding: utf-8 -*-
"""CS item analysis API schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from api.v1.schemas.stocks import KLineData


class CSGoodIdItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    good_id: int
    name: str
    market_hash_name: str = ""


class CSItemSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: List[CSGoodIdItem] = Field(default_factory=list)
    page_index: int = 1
    page_size: int = 20
    total: int = 0
    source: Optional[str] = Field(None, description="local | csqaq")


class CSItemCatalogStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_count: int = 0
    api_total: int = 0
    last_full_sync_at: Optional[str] = None
    last_incremental_sync_at: Optional[str] = None
    last_sync_status: str = "idle"
    last_sync_mode: str = ""
    checkpoint_page: int = 0
    checkpoint_mode: str = ""
    last_error: str = ""
    local_search_enabled: bool = True


class CSItemCatalogSyncResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mode: str
    pages_fetched: int = 0
    rows_upserted: int = 0
    api_total: int = 0
    previous_api_total: Optional[int] = None
    resume: Optional[bool] = None
    max_pages: Optional[int] = None
    completed: Optional[bool] = None


class CSItemAnalyzeRequest(BaseModel):
    good_id: Optional[int] = Field(None, description="CSQAQ good_id")
    item: Optional[str] = Field(None, description="Item name or market_hash_name query")
    platform: Optional[str] = Field(None, description="buff | yyyp | steam")
    period: int = Field(365, ge=30, le=730)
    prefer_crawl: bool = Field(True, description="Merge crawler K-line volume when available")
    refresh_crawl: bool = Field(False, description="Run full Playwright K-line crawl before analyze")
    refresh_today: bool = Field(
        True,
        description="When refresh_crawl is false, lightly re-crawl latest bars (incl. today) before merge",
    )
    kline_pages: int = Field(5, ge=1, le=20)
    include_report: bool = Field(True, description="Generate LLM/template Markdown report")
    skills: Optional[List[str]] = Field(
        None,
        description="Trading skill ids for CS report (default bull_trend). See GET /api/v1/cs/items/skills",
    )


class CSItemSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    market_hash_name: Optional[str] = None
    buff_sell_price: Optional[float] = None
    yyyp_sell_price: Optional[float] = None
    steam_sell_price: Optional[float] = None
    buff_sell_num: Optional[int] = None
    yyyp_sell_num: Optional[int] = None
    turnover_number: Optional[float] = None
    updated_at: Optional[str] = None


class CSItemMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    good_id: int
    item_name: str
    market_hash_name: str
    platform: Any
    ohlc_source: str
    volume_source: str
    data_quality: str
    row_count: int = 0
    crawl_rows: int = 0
    api_rows: int = 0
    period_days: int = 365


class CSEventIntelItem(BaseModel):
    """CS event intel entry (search snapshot at analyze time)."""

    title: str = Field(..., description="Title")
    snippet: str = Field("", description="Snippet")
    url: str = Field("", description="URL")
    dimension: str = Field("", description="Intel dimension id")
    source: str = Field("", description="Source site")
    published_date: Optional[str] = Field(None, description="Published date if known")


class CSItemTrend(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str
    trend_status: str
    ma_alignment: str = ""
    trend_strength: float = 0.0
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    current_price: float = 0.0
    bias_ma5: float = 0.0
    volume_status: str = ""
    volume_ratio_5d: float = 0.0
    buy_signal: str = ""
    signal_score: int = 0
    signal_reasons: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    macd_status: str = ""
    rsi_status: str = ""
    macd_dif: float = 0.0
    macd_dea: float = 0.0
    rsi_12: float = 0.0


class CSItemContainer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    good_id: Optional[int] = None
    price: Optional[float] = None


class CSReportSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    analysis_summary: str = ""
    operation_advice: str = ""
    trend_prediction: str = ""
    sentiment_score: int = 0


class CSReportStrategy(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ideal_buy: Optional[str] = None
    secondary_buy: Optional[str] = None
    stop_loss: Optional[str] = None
    take_profit: Optional[str] = None


class CSReportBoard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    type: str = ""
    code: str = ""


class CSReportDiagnosticComponent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str = ""
    label: str = ""
    status: str = "unknown"
    message: str = ""


class CSReportDiagnostics(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "unknown"
    status_label: str = ""
    reason: str = ""
    components: Dict[str, CSReportDiagnosticComponent] = Field(default_factory=dict)
    copy_text: str = ""


class CSReportPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: CSReportSummary = Field(default_factory=CSReportSummary)
    strategy: CSReportStrategy = Field(default_factory=CSReportStrategy)
    diagnostics: CSReportDiagnostics = Field(default_factory=CSReportDiagnostics)
    containers: List[CSItemContainer] = Field(default_factory=list)
    belong_boards: List[CSReportBoard] = Field(default_factory=list)


class CSItemAnalyzeResponse(BaseModel):
    good_id: int
    item_name: str
    market_hash_name: str
    platform: str
    snapshot: CSItemSnapshot
    meta: CSItemMeta
    trend: CSItemTrend
    ohlcv: List[KLineData]
    report_markdown: str = ""
    report_source: Literal["llm", "template", "none"] = "none"
    report: CSReportPayload = Field(default_factory=CSReportPayload)
    event_intel: List[CSEventIntelItem] = Field(
        default_factory=list,
        description="Event intel items fetched during this analyze run",
    )
    event_context: str = Field(
        "",
        description="Formatted event intel text fed to the report generator",
    )
    active_skills: List[str] = Field(
        default_factory=list,
        description="Skill ids activated in GeminiAnalyzer.analyze() system prompt (stock-equivalent path)",
    )


class CSChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str
    session_id: Optional[str] = None
    skills: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Optional context: scope (market|portfolio|single_item|general), "
            "good_id, item_name, platform, previous_analysis_summary"
        ),
    )


class CSChatResponse(BaseModel):
    success: bool
    content: str
    session_id: str
    error: Optional[str] = None


class CSChatSessionItem(BaseModel):
    session_id: str
    title: str
    message_count: int
    created_at: Optional[str] = None
    last_active: Optional[str] = None


class CSChatSessionsResponse(BaseModel):
    sessions: List[CSChatSessionItem] = Field(default_factory=list)


class CSChatSessionMessagesResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    linked_item: Optional[Dict[str, Any]] = None


class CSHoldingCreateRequest(BaseModel):
    item_name: str
    good_id: Optional[int] = None
    market_hash_name: str = ""
    wear: str = ""
    float_value: Optional[float] = Field(None, ge=0, le=1)
    platform: Optional[str] = "yyyp"
    quantity: int = Field(1, ge=1)
    purchase_price: float = Field(0.0, ge=0)
    market_price: Optional[float] = Field(None, ge=0)
    note: str = ""


class CSHoldingUpdateRequest(BaseModel):
    item_name: Optional[str] = None
    good_id: Optional[int] = None
    market_hash_name: Optional[str] = None
    wear: Optional[str] = None
    float_value: Optional[float] = Field(None, ge=0, le=1)
    platform: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=1)
    purchase_price: Optional[float] = Field(None, ge=0)
    market_price: Optional[float] = Field(None, ge=0)
    note: Optional[str] = None


class CSHoldingBulkCreateRequest(BaseModel):
    items: List[CSHoldingCreateRequest] = Field(default_factory=list)


class CSHoldingSummary(BaseModel):
    item_count: int = 0
    row_count: int = 0
    total_market_value: Optional[float] = None
    total_cost: float = 0.0
    total_pnl: Optional[float] = None


class CSHoldingItem(BaseModel):
    id: int
    good_id: Optional[int] = None
    item_name: str
    market_hash_name: str = ""
    wear: str = ""
    float_value: Optional[float] = None
    platform: str = "yyyp"
    quantity: int = 1
    purchase_price: float = 0.0
    market_price: Optional[float] = None
    cost_total: float = 0.0
    market_total: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    thumbnail_url: Optional[str] = None
    note: Optional[str] = None
    dedup_key: Optional[str] = None
    import_batch_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CSHoldingsPagination(BaseModel):
    page: int = 1
    page_size: int = 50
    total: int = 0


class CSHoldingsSnapshotResponse(BaseModel):
    summary: CSHoldingSummary
    items: List[CSHoldingItem] = Field(default_factory=list)
    pagination: Optional[CSHoldingsPagination] = None


class CSExtractedHoldingItem(BaseModel):
    item_name: str = ""
    weapon_name: str = ""
    skin_name: str = ""
    wear: str = ""
    market_price: Optional[float] = None
    purchase_price: Optional[float] = None
    pnl: Optional[float] = None
    confidence: str = "medium"
    good_id: Optional[int] = None


class CSHoldingsExtractResponse(BaseModel):
    summary: Dict[str, Any] = Field(default_factory=dict)
    items: List[CSExtractedHoldingItem] = Field(default_factory=list)
    raw_text: Optional[str] = None


class CSHoldingDraftItem(BaseModel):
    draft_id: str
    source: Literal["manual", "vision", "csv"] = "manual"
    item_name: str
    wear: str = ""
    float_value: Optional[float] = None
    platform: str = "yyyp"
    quantity: int = 1
    purchase_price: float = 0.0
    market_price: Optional[float] = None
    good_id: Optional[int] = None
    market_hash_name: str = ""
    match_tier: str = "none"
    match_confidence: str = "low"
    match_score: float = 0.0
    vision_confidence: str = "medium"
    dedup_key: str = ""
    duplicate_of: Optional[int] = None
    checked: bool = True
    candidates: List[Dict[str, Any]] = Field(default_factory=list)


class CSHoldingsImportPreviewItem(BaseModel):
    item_name: str
    wear: str = ""
    float_value: Optional[float] = Field(None, ge=0, le=1)
    platform: Optional[str] = "yyyp"
    quantity: int = Field(1, ge=1)
    purchase_price: float = Field(0.0, ge=0)
    market_price: Optional[float] = Field(None, ge=0)
    good_id: Optional[int] = None
    confidence: str = "medium"


class CSHoldingsImportPreviewRequest(BaseModel):
    source: Literal["manual", "vision", "csv"] = "manual"
    items: List[CSHoldingsImportPreviewItem] = Field(default_factory=list)


class CSHoldingsImportPreviewSummary(BaseModel):
    draft_count: int = 0
    duplicate_count: int = 0
    low_confidence_count: int = 0
    checked_count: int = 0


class CSHoldingsImportPreviewResponse(BaseModel):
    session_id: str
    source: str
    summary: CSHoldingsImportPreviewSummary
    drafts: List[CSHoldingDraftItem] = Field(default_factory=list)
    vision_summary: Optional[Dict[str, Any]] = None


class CSHoldingsImportUpdateRequest(BaseModel):
    session_id: str
    drafts: List[CSHoldingDraftItem] = Field(default_factory=list)
    rematch: bool = True


class CSHoldingsImportCommitRequest(BaseModel):
    session_id: str
    draft_ids: Optional[List[str]] = None
    skip_duplicates: bool = False


class CSHoldingsImportCommitResponse(CSHoldingsSnapshotResponse):
    batch_id: str
    imported_count: int = 0
    skipped_duplicates: int = 0


class CSHoldingsRiskResponse(BaseModel):
    as_of: str
    platform: str = "all"
    summary: Dict[str, Any] = Field(default_factory=dict)
    thresholds: Dict[str, Any] = Field(default_factory=dict)
    concentration: Dict[str, Any] = Field(default_factory=dict)
    stop_loss: Dict[str, Any] = Field(default_factory=dict)
    price_stale: Dict[str, Any] = Field(default_factory=dict)
    platform_exposure: Dict[str, Any] = Field(default_factory=dict)
    top_gainers: List[Dict[str, Any]] = Field(default_factory=list)
    top_losers: List[Dict[str, Any]] = Field(default_factory=list)
