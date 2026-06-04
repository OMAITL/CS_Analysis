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
