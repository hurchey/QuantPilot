from __future__ import annotations

import math
from typing import Any

from .types import BacktestResult, EquityPoint, TradeEvent


def trade_event_from_db_row(
    row: Any,
) -> TradeEvent:
    """Convert DB Trade row to TradeEvent."""
    return TradeEvent(
        timestamp=row.timestamp,
        symbol=row.symbol,
        side=row.side,
        qty=float(row.qty),
        price=float(row.price),
        fee=float(row.fee or 0),
        realized_pnl=float(row.realized_pnl) if row.realized_pnl is not None else None,
        reason=None,
    )


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def trade_to_dict(trade: TradeEvent) -> dict[str, Any]:
    return {
        "timestamp": trade.timestamp.isoformat(),
        "symbol": trade.symbol,
        "side": trade.side,
        "qty": float(trade.qty),
        "price": float(trade.price),
        "fee": float(trade.fee),
        "realized_pnl": None if trade.realized_pnl is None else float(trade.realized_pnl),
        "reason": trade.reason,
    }


def equity_point_to_dict(point: EquityPoint) -> dict[str, Any]:
    return {
        "timestamp": point.timestamp.isoformat(),
        "equity": float(point.equity),
        "cash": float(point.cash),
        "position_qty": float(point.position_qty),
        "position_avg_price": float(point.position_avg_price),
        "drawdown": float(point.drawdown),
    }


def result_to_json_payload(result: BacktestResult) -> dict[str, Any]:
    return {
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "config": {k: _json_safe_value(v) for k, v in result.config.items()},
        "metrics": {k: _json_safe_value(v) for k, v in result.metrics.items()},
        "meta": {k: _json_safe_value(v) for k, v in result.meta.items()},
        "trades": [trade_to_dict(t) for t in result.trades],
        "equity_curve": [equity_point_to_dict(p) for p in result.equity_curve],
    }


def build_db_rows_for_result(
    *,
    backtest_run_id: int,
    result: BacktestResult,
) -> dict[str, Any]:
    """
    Returns insert-ready rows you can use with your ORM models.
    """
    trade_rows = [
        {
            "backtest_run_id": backtest_run_id,
            "symbol": t.symbol,
            "side": t.side,
            "qty": float(t.qty),
            "price": float(t.price),
            "timestamp": t.timestamp,
            "fee": float(t.fee),
            "realized_pnl": None if t.realized_pnl is None else float(t.realized_pnl),
        }
        for t in result.trades
    ]

    equity_rows = [
        {
            "backtest_run_id": backtest_run_id,
            "timestamp": p.timestamp,
            "equity": float(p.equity),
            "drawdown": float(p.drawdown),
        }
        for p in result.equity_curve
    ]

    return {
        "metrics_json": {k: _json_safe_value(v) for k, v in result.metrics.items()},
        "trade_rows": trade_rows,
        "equity_rows": equity_rows,
        "meta_json": {k: _json_safe_value(v) for k, v in result.meta.items()},
    }