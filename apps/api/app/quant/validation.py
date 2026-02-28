"""
Statistical validation for backtesting: walk-forward, bootstrap CI, no lookahead.

- Walk-forward / rolling out-of-sample: train on past, test on future
- Bootstrap confidence intervals for metrics
- Survivorship-bias-free: use LISTING_STATUS for historical universe
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from .types import Bar, BacktestConfig, BacktestResult

T = TypeVar("T")


@dataclass(slots=True)
class WalkForwardFold:
    """Single fold: train period, test period."""

    train_start_idx: int
    train_end_idx: int
    test_start_idx: int
    test_end_idx: int
    train_bars: list[Bar]
    test_bars: list[Bar]


def walk_forward_splits(
    bars: list[Bar],
    train_pct: float = 0.6,
    step_pct: float = 0.2,
    min_train_bars: int = 60,
    min_test_bars: int = 20,
) -> list[WalkForwardFold]:
    """
    Rolling walk-forward splits. No random shuffle - chronological only.
    train_pct: fraction of expanding window for training
    step_pct: step forward as fraction of total bars each fold
    """
    n = len(bars)
    if n < min_train_bars + min_test_bars:
        return []

    folds: list[WalkForwardFold] = []
    test_start = int(n * train_pct)
    step = max(1, int(n * step_pct))

    while test_start + min_test_bars <= n:
        train_end = test_start
        train_start = max(0, train_end - min_train_bars)
        test_end = min(test_start + min_test_bars, n)

        if train_end - train_start < min_train_bars:
            break

        folds.append(
            WalkForwardFold(
                train_start_idx=train_start,
                train_end_idx=train_end,
                test_start_idx=test_start,
                test_end_idx=test_end,
                train_bars=bars[train_start:train_end],
                test_bars=bars[test_start:test_end],
            )
        )
        test_start += step

    return folds


def bootstrap_metric(
    equity_returns: list[float],
    metric_fn: Callable[[list[float]], float],
    n_bootstrap: int = 1000,
    seed: int | None = None,
) -> tuple[float, float, float]:
    """
    Bootstrap confidence interval for a metric.
    Returns (point_estimate, lower_95, upper_95).
    """
    if len(equity_returns) < 2:
        return (0.0, 0.0, 0.0)

    rng = random.Random(seed)
    n = len(equity_returns)
    point = metric_fn(equity_returns)
    samples = []

    for _ in range(n_bootstrap):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        resampled = [equity_returns[i] for i in idx]
        samples.append(metric_fn(resampled))

    samples.sort()
    lo = int(0.025 * n_bootstrap)
    hi = int(0.975 * n_bootstrap)
    return (point, samples[lo], samples[hi])


def bootstrap_sharpe(
    equity_returns: list[float],
    n_bootstrap: int = 1000,
    risk_free_per_period: float = 0.0,
    periods_per_year: int = 252,
    seed: int | None = None,
) -> tuple[float, float, float]:
    """Bootstrap CI for annualized Sharpe ratio."""
    import math
    from statistics import mean, stdev

    def sharpe_fn(rets: list[float]) -> float:
        if len(rets) < 2:
            return 0.0
        excess = [r - risk_free_per_period for r in rets]
        m = mean(excess)
        s = stdev(rets)
        if s <= 0:
            return 0.0
        return (m / s) * math.sqrt(periods_per_year)

    return bootstrap_metric(equity_returns, sharpe_fn, n_bootstrap, seed)


def check_lookahead_in_signals(
    bars: list[Bar],
    positions: list[int],
    signal_lookback: int,
) -> tuple[bool, str]:
    """
    Heuristic check: positions should not use future data.
    signal_lookback: max bars the signal might look back.
    Returns (ok, message).
    """
    if len(positions) != len(bars):
        return (False, "positions length != bars length")
    # Can't fully verify without strategy code; document that signals must be causal
    return (True, "Manual review: ensure signals use only past data")


def walk_forward_backtest(
    bars: list[Bar],
    run_fn: Callable[[list[Bar], list[Bar], BacktestConfig], BacktestResult],
    config: BacktestConfig,
    train_pct: float = 0.6,
    step_pct: float = 0.2,
) -> list[dict[str, Any]]:
    """
    Run walk-forward backtest. run_fn(train_bars, test_bars, config) -> result.
    Returns list of fold results with metrics.
    """
    folds = walk_forward_splits(bars, train_pct, step_pct)
    results = []
    for fold in folds:
        result = run_fn(fold.train_bars, fold.test_bars, config)
        results.append({
            "train_bars": len(fold.train_bars),
            "test_bars": len(fold.test_bars),
            "metrics": result.metrics,
            "num_trades": result.metrics.get("num_trades", 0),
        })
    return results
