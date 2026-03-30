# apps/api/app/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =========================
# Shared / Generic
# =========================

class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


# =========================
# Auth Schemas
# =========================

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=512)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=512)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Email is required")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: Optional[datetime] = None


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AuthResponse(BaseModel):
    message: str
    user: UserOut


class MeResponse(BaseModel):
    user: UserOut
    workspace: Optional[WorkspaceOut] = None


# =========================
# Strategy Schemas
# =========================

StrategyType = Literal["sma_crossover"]


class StrategyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    strategy_type: str = Field(min_length=1, max_length=100)
    symbol: str = Field(min_length=1, max_length=50)
    timeframe: str = Field(default="1d", min_length=1, max_length=20)
    parameters_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name is required")
        return v

    @field_validator("strategy_type")
    @classmethod
    def clean_strategy_type(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("strategy_type is required")
        return v

    @field_validator("symbol")
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("symbol is required")
        return v

    @field_validator("timeframe")
    @classmethod
    def clean_timeframe(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("timeframe is required")
        return v


class StrategyCreateRequest(StrategyBase):
    pass


class StrategyUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    strategy_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    symbol: Optional[str] = Field(default=None, min_length=1, max_length=50)
    timeframe: Optional[str] = Field(default=None, min_length=1, max_length=20)
    parameters_json: Optional[dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("strategy_type")
    @classmethod
    def clean_strategy_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("strategy_type cannot be empty")
        return v

    @field_validator("symbol")
    @classmethod
    def clean_symbol(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if not v:
            raise ValueError("symbol cannot be empty")
        return v

    @field_validator("timeframe")
    @classmethod
    def clean_timeframe(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("timeframe cannot be empty")
        return v


class StrategyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    name: str
    strategy_type: str
    symbol: str
    timeframe: str
    parameters_json: dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class StrategySummaryOut(BaseModel):
    id: int
    name: str
    symbol: str
    timeframe: str
    strategy_type: str
    parameters_json: dict[str, Any] = Field(default_factory=dict)


# =========================
# Data / Market Bar Schemas
# =========================

class UploadDataResponse(BaseModel):
    message: str
    symbol: str
    timeframe: str
    rows_inserted: int
    rows_skipped_duplicates: int
    uploaded_at: str


class SymbolTimeframeOut(BaseModel):
    symbol: str
    timeframe: str


class MarketBarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


# =========================
# Backtest Schemas
# =========================

class BacktestRunRequest(BaseModel):
    strategy_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = Field(default=10_000.0, gt=0)
    fees_bps: float = Field(default=1.0, ge=0)
    slippage_bps: float = Field(default=1.0, ge=0)


class BacktestRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    strategy_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float
    fees_bps: float
    slippage_bps: float
    status: str
    metrics_json: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BacktestRunMetaOut(BaseModel):
    strategy_type: str
    symbol: str
    timeframe: str
    fast_window: int
    slow_window: int
    bars_used: int


class BacktestRunCreateResponse(BaseModel):
    message: str
    run: BacktestRunOut
    meta: BacktestRunMetaOut


class BacktestRunDetailResponse(BaseModel):
    run: BacktestRunOut
    strategy: Optional[StrategySummaryOut] = None


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backtest_run_id: int
    symbol: str
    side: str
    qty: float
    price: float
    timestamp: datetime
    fee: float
    realized_pnl: Optional[float] = None


class EquityPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backtest_run_id: int
    timestamp: datetime
    equity: float
    drawdown: float


class BacktestMetricsOut(BaseModel):
    # Loose/JSON-friendly metric shape
    model_config = ConfigDict(extra="allow")


# =========================
# Dashboard Schemas
# =========================

class DashboardSummaryResponse(BaseModel):
    strategies_count: int
    backtests_count: int
    latest_run_id: Optional[int] = None
    latest_status: Optional[str] = None
    latest_metrics: dict[str, Any] = Field(default_factory=dict)
    best_sharpe: Optional[float] = None
    best_total_return: Optional[float] = None


class DashboardRiskResponse(BaseModel):
    latest_run_id: Optional[int] = None
    sharpe: Optional[float] = None
    volatility: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None


class PerformancePointOut(BaseModel):
    timestamp: Optional[str] = None
    equity: float
    drawdown: float


class RecentRunOut(BaseModel):
    id: int
    strategy_id: int
    created_at: Optional[str] = None
    status: str
    total_return: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None


class DashboardPerformanceResponse(BaseModel):
    latest_run_id: Optional[int] = None
    equity_curve: list[PerformancePointOut] = Field(default_factory=list)
    recent_runs: list[RecentRunOut] = Field(default_factory=list)