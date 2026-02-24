from __future__ import annotations

from .indicators import sma
from .types import Bar


def generate_sma_crossover_positions(
    bars: list[Bar],
    fast_window: int,
    slow_window: int,
    shift_for_execution: bool = True,
) -> dict[str, list[int] | list[float | None]]:
    """
    Returns desired positions:
      1 = long
      0 = flat

    By default, shifts positions forward by 1 bar to avoid lookahead bias:
    signal computed on bar i is applied at bar i+1.
    """
    if fast_window <= 0 or slow_window <= 0:
        raise ValueError("fast_window and slow_window must be > 0")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be < slow_window")
    if not bars:
        return {"positions": [], "fast_sma": [], "slow_sma": []}

    closes = [float(b.close) for b in bars]
    fast = sma(closes, fast_window)
    slow = sma(closes, slow_window)

    raw_positions: list[int] = []
    for f, s in zip(fast, slow):
        if f is None or s is None:
            raw_positions.append(0)
        else:
            raw_positions.append(1 if f > s else 0)

    if shift_for_execution and raw_positions:
        positions = [0] + raw_positions[:-1]
    else:
        positions = raw_positions

    return {
        "positions": positions,
        "fast_sma": fast,
        "slow_sma": slow,
    }