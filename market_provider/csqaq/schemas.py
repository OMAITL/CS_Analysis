# -*- coding: utf-8 -*-
"""Pydantic models for CSQAQ API payloads and normalized CS item series."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CSQAQPlatform(IntEnum):
    """Trading platform identifiers used by CSQAQ chart APIs."""

    BUFF = 1
    YYYP = 2  # 悠悠有品 – default primary platform for CN market decisions
    STEAM = 3


ChartMetricKey = Literal[
    "sell_price",
    "buy_price",
    "sell_num",
    "buy_num",
    "lease_num",
    "short_lease_price",
    "long_lease_price",
    "lease_annual",
    "long_lease_annual",
    "turnover_number",
    "transfer_price",
]

IndexKlinePeriod = Literal["1hour", "4hour", "1day", "7day"]


class CSQAQResponse(BaseModel):
    """Common CSQAQ envelope."""

    model_config = ConfigDict(extra="ignore")

    code: int
    msg: str
    data: Any = None


class GoodIdEntry(BaseModel):
    """Single item identity row from get_good_id / suggest APIs."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    market_hash_name: str


class GoodIdSearchResult(BaseModel):
    """Paginated good-id search payload."""

    model_config = ConfigDict(extra="ignore")

    items: List[GoodIdEntry] = Field(default_factory=list)
    page_index: int = 1
    page_size: int = 20
    total: int = 0


class CSQAQChartSeries(BaseModel):
    """
    Normalized time series from POST /api/v1/info/chart.

    ``main_data`` holds the requested metric (e.g. sell_price).
    ``num_data`` is populated when ``key=sell_price`` (companion sell_num series).
    """

    model_config = ConfigDict(extra="ignore")

    good_id: int
    key: ChartMetricKey
    platform: CSQAQPlatform
    period: int
    style: str = "all_style"
    timestamps: List[int] = Field(default_factory=list)
    main_data: List[Optional[float]] = Field(default_factory=list)
    num_data: List[Optional[int]] = Field(default_factory=list)

    @field_validator("timestamps", mode="before")
    @classmethod
    def _coerce_timestamps(cls, value: Any) -> List[int]:
        if value is None:
            return []
        return [int(v) for v in value]

    @classmethod
    def from_api_payload(
        cls,
        *,
        good_id: int,
        key: ChartMetricKey,
        platform: CSQAQPlatform,
        period: int,
        style: str,
        payload: Dict[str, Any],
    ) -> "CSQAQChartSeries":
        data = payload or {}
        return cls(
            good_id=good_id,
            key=key,
            platform=platform,
            period=period,
            style=style,
            timestamps=list(data.get("timestamp") or []),
            main_data=list(data.get("main_data") or []),
            num_data=list(data.get("num_data") or []),
        )


class IndexKlineBar(BaseModel):
    """Single OHLCV bar from GET /api/v1/sub/kline."""

    model_config = ConfigDict(extra="ignore")

    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: int

    @classmethod
    def from_api_row(cls, row: Dict[str, Any]) -> "IndexKlineBar":
        return cls(
            timestamp_ms=int(row["t"]),
            open=float(row["o"]),
            high=float(row["h"]),
            low=float(row["l"]),
            close=float(row["c"]),
            volume=int(row.get("v") or 0),
        )


class ItemOhlcvBuildMeta(BaseModel):
    """Metadata describing how an item chart was converted to OHLCV."""

    model_config = ConfigDict(extra="ignore")

    good_id: int
    price_platform: CSQAQPlatform
    price_key: ChartMetricKey = "sell_price"
    volume_source: Literal["turnover_number", "sell_num", "index_native", "none"]
    volume_platform: Optional[CSQAQPlatform] = None
    period_days: int
    style: str = "all_style"
    row_count: int = 0


OhlcSource = Literal["kline_chart_all", "sell_price_agg", "mixed"]
MergedVolumeSource = Literal[
    "kline_chart_all_v",
    "turnover_number",
    "sell_num",
    "none",
]
DataQuality = Literal["full", "price_only", "degraded"]


class MergedItemOhlcvMeta(BaseModel):
    """Metadata for API + crawler fused item OHLCV."""

    model_config = ConfigDict(extra="ignore")

    good_id: int
    item_name: str
    market_hash_name: str
    platform: CSQAQPlatform
    ohlc_source: OhlcSource
    volume_source: MergedVolumeSource
    data_quality: DataQuality
    row_count: int = 0
    crawl_rows: int = 0
    api_rows: int = 0
    period_days: int = 365
