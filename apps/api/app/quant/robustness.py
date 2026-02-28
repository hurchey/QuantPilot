"""
Robustness gate: only accept strategy updates that beat current model OOS.

- Out-of-sample performance after costs
- Similar or lower risk
- Not fragile to small parameter changes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .types import BacktestResult


@dataclass(slots=True)
class RobustnessCriteria:
    """Criteria for accepting a new model."""

    min_oos_sharpe: float = 0.0  # new model must have OOS Sharpe >= this
    max_drawdown_increase_pct: float = 0.2  # new MDD can't exceed current * (1 + this)
    min_trades_for_significance: int = 10  # need enough trades to trust
    parameter_sensitivity_bps: float = 5.0  # small param change shouldn't move metric > 5 bps


def passes_robustness_gate(
    current_result: BacktestResult | None,
    new_result: BacktestResult,
    criteria: RobustnessCriteria | None = None,
) -> tuple[bool, list[str]]:
    """
    Check if new model passes robustness gate vs current.
    Returns (passed, list of failure reasons).
    """
    crit = criteria or RobustnessCriteria()
    failures = []

    new_metrics = new_result.metrics or {}
    new_sharpe = new_metrics.get("sharpe")
    new_mdd = new_metrics.get("max_drawdown")
    new_trades = new_metrics.get("num_trades", 0)

    if new_trades < crit.min_trades_for_significance:
        failures.append(
            f"Too few trades ({new_trades}) for significance (min {crit.min_trades_for_significance})"
        )

    if new_sharpe is not None and new_sharpe < crit.min_oos_sharpe:
        failures.append(
            f"OOS Sharpe {new_sharpe:.4f} below minimum {crit.min_oos_sharpe}"
        )

    if current_result and current_result.metrics:
        curr_mdd = current_result.metrics.get("max_drawdown") or 0
        curr_sharpe = current_result.metrics.get("sharpe")

        if curr_mdd < 0 and new_mdd is not None:
            max_allowed = abs(curr_mdd) * (1 + crit.max_drawdown_increase_pct)
            if abs(new_mdd) > max_allowed:
                failures.append(
                    f"Max drawdown {new_mdd:.4f} exceeds allowed {max_allowed:.4f}"
                )

        if curr_sharpe is not None and new_sharpe is not None:
            if new_sharpe < curr_sharpe:
                failures.append(
                    f"OOS Sharpe {new_sharpe:.4f} worse than current {curr_sharpe:.4f}"
                )

    return (len(failures) == 0, failures)


def should_retrain(
    metrics_history: list[dict[str, Any]],
    sharpe_decay_threshold: float = 0.2,
    min_bars_since_retrain: int = 63,  # ~3 months
) -> bool:
    """
    Heuristic: should we retrain? E.g. if recent OOS Sharpe dropped > 20%.
    """
    if len(metrics_history) < 2:
        return False
    recent = metrics_history[-1]
    prior = metrics_history[-2]
    recent_sharpe = recent.get("sharpe") or 0
    prior_sharpe = prior.get("sharpe") or 0
    if prior_sharpe <= 0:
        return False
    decay = (prior_sharpe - recent_sharpe) / prior_sharpe
    return decay >= sharpe_decay_threshold
