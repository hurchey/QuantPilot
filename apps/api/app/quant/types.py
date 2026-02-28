from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(slots=True)
class TradeEvent:
    timestamp: datetime
    symbol: str
    side: str  # "buy" | "sell"
    qty: float
    price: float
    fee: float
    realized_pnl: float | None = None
    reason: str | None = None


@dataclass(slots=True)
class EquityPoint:
    timestamp: datetime
    equity: float
    cash: float
    position_qty: float
    position_avg_price: float
    drawdown: float = 0.0


@dataclass(slots=True)
class BacktestConfig:
    symbol: str
    timeframe: str = "1d"
    initial_capital: float = 10_000.0
    fees_bps: float = 1.0
    slippage_bps: float = 1.0
    spread_bps: float = 0.0  # bid-ask half-spread
    fixed_qty: float | None = None
    allow_fractional: bool = True
    close_final_position: bool = True
    risk_free_rate: float = 0.0  # annualized, e.g. 0.02 for 2%
    periods_per_year: int = 252  # daily default

    # Realistic execution (quant finance)
    adv_dollars: float = 0.0  # avg daily volume $ for impact; 0 = no impact
    impact_coef: float = 0.1  # sqrt impact coefficient
    borrow_rate_bps: float = 0.0  # short borrow cost
    max_position_pct_adv: float = 0.1  # max position as % of ADV (liquidity limit)
    max_leverage: float = 1.0  # 1 = no margin, 2 = 2x
    execution_delay_bars: int = 0  # bars before order fills (no lookahead)


@dataclass(slots=True)
class BacktestResult:
    symbol: str
    timeframe: str
    config: dict[str, Any]
    metrics: dict[str, Any]
    trades: list[TradeEvent] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)