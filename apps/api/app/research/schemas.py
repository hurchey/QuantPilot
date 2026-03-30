# apps/api/app/research/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Scan request/response ---


class ScanRequest(BaseModel):
    """Request to scan a list of symbols for extreme dislocations."""

    symbols: list[str] = Field(
        ...,
        description="List of ticker symbols to scan (e.g. ['AAPL', 'GME'])",
        min_length=1,
    )
    start_date: str = Field(
        default="2010-01-01",
        description="Start of historical window (YYYY-MM-DD)",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End of historical window (YYYY-MM-DD). Defaults to today.",
    )
    min_return_3d_pct: float = Field(
        default=500.0,
        description="Minimum 3-day return percentage to qualify as a dislocation",
        ge=100.0,
    )


class ScanSymbolListRequest(BaseModel):
    """Request to scan a predefined universe."""

    universe: str = Field(
        default="sp500",
        description="Predefined universe: 'sp500', 'russell2000', 'all_us', or 'custom'",
    )
    custom_symbols: Optional[list[str]] = Field(
        default=None,
        description="Custom symbol list (required if universe='custom')",
    )
    start_date: str = Field(default="2010-01-01")
    end_date: Optional[str] = None
    min_return_3d_pct: float = Field(default=500.0, ge=100.0)


class ScanResult(BaseModel):
    symbol: str
    event_start_date: str
    return_3d_pct: float
    return_1d_pct: Optional[float] = None
    price_start: float
    price_peak: float
    label_a: bool
    label_b: bool


class ScanResponse(BaseModel):
    total_symbols_scanned: int
    total_events_found: int
    events: list[ScanResult]
    errors: list[str] = Field(default_factory=list)


# --- Event detail ---


class DislocationEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    company_name: Optional[str] = None
    security_type: Optional[str] = None

    event_start_date: datetime
    event_end_date: datetime
    peak_date: Optional[datetime] = None

    price_start: float
    price_peak: float
    price_end_3d: Optional[float] = None
    return_1d_pct: Optional[float] = None
    return_3d_pct: float
    return_peak_pct: Optional[float] = None

    label_a: int
    label_b: int
    day_after_continuation: Optional[int] = None

    volume_event_day: Optional[float] = None
    volume_avg_20d_pre: Optional[float] = None
    volume_ratio: Optional[float] = None

    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None
    market_cap_pre: Optional[float] = None
    short_interest_shares: Optional[float] = None
    short_pct_float: Optional[float] = None
    days_to_cover: Optional[float] = None

    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    ipo_date: Optional[datetime] = None
    days_since_ipo: Optional[int] = None

    catalyst_summary: Optional[str] = None
    news_count_event_day: Optional[int] = None

    options_available: Optional[int] = None
    iv_pre_event: Optional[float] = None
    call_oi_pre: Optional[float] = None
    put_oi_pre: Optional[float] = None

    taxonomy_bucket: Optional[str] = None
    taxonomy_confidence: Optional[float] = None
    taxonomy_notes: Optional[str] = None

    data_source: Optional[str] = None
    created_at: Optional[datetime] = None


class DislocationFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    feature_name: str
    feature_value: Optional[str] = None
    feature_numeric: Optional[float] = None
    feature_json: Optional[Any] = None


class DislocationEventDetailOut(BaseModel):
    event: DislocationEventOut
    features: list[DislocationFeatureOut] = Field(default_factory=list)


# --- Enrich / classify ---


class EnrichRequest(BaseModel):
    """Request to enrich events with float, volume, fundamentals."""

    event_ids: Optional[list[int]] = Field(
        default=None,
        description="Specific event IDs to enrich. If None, enriches all un-enriched events.",
    )


class ClassifyRequest(BaseModel):
    """Request to assign taxonomy buckets."""

    event_ids: Optional[list[int]] = Field(
        default=None,
        description="Specific event IDs to classify. If None, classifies all unclassified events.",
    )


class EnrichResponse(BaseModel):
    events_enriched: int
    errors: list[str] = Field(default_factory=list)


class ClassifyResponse(BaseModel):
    events_classified: int
    bucket_counts: dict[str, int] = Field(default_factory=dict)


# --- Dataset export ---


class DatasetExportRequest(BaseModel):
    format: str = Field(default="json", description="'json' or 'csv'")
    label: Optional[str] = Field(
        default=None,
        description="Filter: 'A' for 500%+, 'B' for 1000%+, None for all",
    )
    taxonomy_bucket: Optional[str] = Field(
        default=None,
        description="Filter by taxonomy bucket",
    )


class DatasetStatsOut(BaseModel):
    total_events: int
    label_a_count: int
    label_b_count: int
    continuation_rate: Optional[float] = None
    bucket_distribution: dict[str, int] = Field(default_factory=dict)
    top_symbols: list[dict[str, Any]] = Field(default_factory=list)
