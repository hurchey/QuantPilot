from __future__ import annotations

import math
from statistics import mean, stdev

from .types import Bar, EquityPoint, TradeEvent


def _safe_float(x: float | int | None) -> float | None:
    if x is None:
        return None
    v = float(x)
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def equity_returns(equity_curve: list[EquityPoint]) -> list[float]:
    if len(equity_curve) < 2:
        return []
    out: list[float] = []
    for prev, curr in zip(equity_curve[:-1], equity_curve[1:]):
        if prev.equity == 0:
            out.append(0.0)
        else:
            out.append((curr.equity / prev.equity) - 1.0)
    return out


def max_drawdown(equity_curve: list[EquityPoint]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0].equity
    mdd = 0.0
    for p in equity_curve:
        peak = max(peak, p.equity)
        dd = (p.equity / peak) - 1.0 if peak > 0 else 0.0
        mdd = min(mdd, dd)
    return mdd


def compute_metrics(
    *,
    equity_curve: list[EquityPoint],
    trades: list[TradeEvent],
    bars: list[Bar],
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> dict[str, float | int | None]:
    if not equity_curve:
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe": None,
            "max_drawdown": 0.0,
            "win_rate": None,
            "profit_factor": None,
            "num_trades": 0,
            "num_round_trips": 0,
            "benchmark_return": None,
        }

    start_equity = equity_curve[0].equity
    end_equity = equity_curve[-1].equity
    total_return = (end_equity / start_equity - 1.0) if start_equity > 0 else 0.0

    rets = equity_returns(equity_curve)

    annualized_return: float | None = None
    volatility: float | None = None
    sharpe: float | None = None

    if rets:
        n_periods = len(rets)
        if start_equity > 0 and end_equity > 0 and periods_per_year > 0:
            annualized_return = (end_equity / start_equity) ** (periods_per_year / max(n_periods, 1)) - 1.0

        if len(rets) >= 2:
            ret_std = stdev(rets)
            volatility = ret_std * math.sqrt(periods_per_year)
            if ret_std > 0:
                per_period_rf = risk_free_rate / periods_per_year
                excess_mean = mean([r - per_period_rf for r in rets])
                sharpe = (excess_mean / ret_std) * math.sqrt(periods_per_year)

    mdd = max_drawdown(equity_curve)

    closed_trades = [t for t in trades if t.side == "sell" and t.realized_pnl is not None]
    wins = [t for t in closed_trades if (t.realized_pnl or 0.0) > 0]
    losses = [t for t in closed_trades if (t.realized_pnl or 0.0) < 0]

    win_rate = (len(wins) / len(closed_trades)) if closed_trades else None

    gross_profit = sum((t.realized_pnl or 0.0) for t in wins)
    gross_loss = abs(sum((t.realized_pnl or 0.0) for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (None if gross_profit == 0 else float("inf"))

    benchmark_return: float | None = None
    if len(bars) >= 2 and bars[0].close:
        benchmark_return = (bars[-1].close / bars[0].close) - 1.0

    return {
        "total_return": _safe_float(total_return),
        "annualized_return": _safe_float(annualized_return),
        "volatility": _safe_float(volatility),
        "sharpe": _safe_float(sharpe),
        "max_drawdown": _safe_float(mdd),
        "win_rate": _safe_float(win_rate),
        "profit_factor": _safe_float(profit_factor),
        "num_trades": len(trades),
        "num_round_trips": len(closed_trades),
        "benchmark_return": _safe_float(benchmark_return),
    }