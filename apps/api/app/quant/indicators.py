from __future__ import annotations

from math import sqrt
from statistics import pstdev
from typing import Sequence


def sma(values: Sequence[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be > 0")

    out: list[float | None] = [None] * len(values)
    if len(values) < window:
        return out

    running_sum = 0.0
    for i, value in enumerate(values):
        running_sum += float(value)
        if i >= window:
            running_sum -= float(values[i - window])
        if i >= window - 1:
            out[i] = running_sum / window
    return out


def ema(values: Sequence[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be > 0")
    if not values:
        return []

    alpha = 2.0 / (window + 1.0)
    out: list[float | None] = [None] * len(values)

    ema_val: float | None = None
    for i, value in enumerate(values):
        v = float(value)
        if ema_val is None:
            ema_val = v
        else:
            ema_val = alpha * v + (1 - alpha) * ema_val

        if i >= window - 1:
            out[i] = ema_val
    return out


def pct_returns(values: Sequence[float]) -> list[float]:
    if len(values) < 2:
        return []
    returns: list[float] = []
    for prev, curr in zip(values[:-1], values[1:]):
        prev_f = float(prev)
        curr_f = float(curr)
        if prev_f == 0:
            returns.append(0.0)
        else:
            returns.append((curr_f / prev_f) - 1.0)
    return returns


def rolling_volatility(values: Sequence[float], window: int) -> list[float | None]:
    rets = pct_returns(values)
    out: list[float | None] = [None] * len(values)
    if window <= 1 or len(rets) < window:
        return out

    # Align vol to price index (returns start at index 1)
    for i in range(window, len(values)):
        window_slice = rets[i - window : i]
        if len(window_slice) < 2:
            out[i] = None
            continue
        out[i] = pstdev(window_slice) * sqrt(window)
    return out