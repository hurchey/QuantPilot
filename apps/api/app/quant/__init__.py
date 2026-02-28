from .types import Bar, BacktestConfig, BacktestResult, EquityPoint, TradeEvent
from .data_loader import load_market_bars
from .signals import generate_sma_crossover_positions
from .backtester import run_backtest, run_sma_crossover_backtest
from .metrics import compute_metrics
from .serializers import (
    trade_to_dict,
    trade_event_from_db_row,
    equity_point_to_dict,
    result_to_json_payload,
    build_db_rows_for_result,
)

__all__ = [
    "Bar",
    "BacktestConfig",
    "BacktestResult",
    "EquityPoint",
    "TradeEvent",
    "load_market_bars",
    "generate_sma_crossover_positions",
    "run_backtest",
    "run_sma_crossover_backtest",
    "compute_metrics",
    "trade_to_dict",
    "trade_event_from_db_row",
    "equity_point_to_dict",
    "result_to_json_payload",
    "build_db_rows_for_result",
]