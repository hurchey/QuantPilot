"""
Volatility indicators for backtesting and stock labeling.

Labels stocks by volatility vs cross-sectional average:
- low: below 0.5x average
- normal: 0.5x - 1.5x average
- high: 1.5x - 2.5x average
- extreme: above 2.5x average
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .types import Bar


@dataclass(slots=True)
class VolatilityProfile:
    """Volatility metrics for a single symbol."""

    symbol: str
    annualized_vol: float  # annualized return std
    realized_vol_20d: float  # 20-day rolling vol
    volatility_label: str  # low, normal, high, extreme
    vs_average: float  # multiple of cross-sectional average (e.g. 1.2 = 20% above avg)
    rank_percentile: float | None  # 0-100, higher = more volatile


def returns_from_bars(bars: list[Bar]) -> list[float]:
    """Compute log returns from close prices."""
    if len(bars) < 2:
        return []
    out = []
    for i in range(1, len(bars)):
        prev = bars[i - 1].close
        curr = bars[i].close
        if prev and prev > 0:
            out.append(math.log(curr / prev))
        else:
            out.append(0.0)
    return out


def realized_volatility(returns: list[float], annualization_factor: float = 252) -> float:
    """
    Annualized volatility (std of returns * sqrt(annualization_factor)).
    For daily data: factor=252. Weekly: 52. Monthly: 12.
    """
    if len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance * annualization_factor)


def rolling_volatility(
    returns: list[float],
    window: int = 20,
    annualization_factor: float = 252,
) -> list[float]:
    """Rolling annualized volatility."""
    out = []
    for i in range(len(returns)):
        start = max(0, i - window + 1)
        window_rets = returns[start : i + 1]
        if len(window_rets) >= 2:
            vol = realized_volatility(window_rets, annualization_factor)
        else:
            vol = 0.0
        out.append(vol)
    return out


def compute_volatility_profile(
    symbol: str,
    bars: list[Bar],
    periods_per_year: int = 252,
    window_days: int = 20,
) -> VolatilityProfile:
    """
    Compute volatility profile for a single symbol.
    """
    rets = returns_from_bars(bars)
    if not rets:
        return VolatilityProfile(
            symbol=symbol,
            annualized_vol=0.0,
            realized_vol_20d=0.0,
            volatility_label="unknown",
            vs_average=0.0,
            rank_percentile=None,
        )

    ann_vol = realized_volatility(rets, float(periods_per_year))
    roll_vols = rolling_volatility(rets, window=min(window_days, len(rets)), annualization_factor=float(periods_per_year))
    vol_20d = roll_vols[-1] if roll_vols else 0.0

    return VolatilityProfile(
        symbol=symbol,
        annualized_vol=ann_vol,
        realized_vol_20d=vol_20d,
        volatility_label="normal",  # will be set by label_volatility_vs_universe
        vs_average=0.0,
        rank_percentile=None,
    )


def label_volatility_vs_universe(
    profiles: list[VolatilityProfile],
) -> list[VolatilityProfile]:
    """
    Label each stock's volatility vs cross-sectional average.
    Updates volatility_label, vs_average, rank_percentile.
    """
    if not profiles:
        return []

    vols = [p.annualized_vol for p in profiles if p.annualized_vol > 0]
    if not vols:
        return profiles

    avg_vol = sum(vols) / len(vols)
    sorted_vols = sorted(vols)
    n = len(sorted_vols)

    for p in profiles:
        if p.annualized_vol <= 0:
            p.volatility_label = "unknown"
            p.vs_average = 0.0
            p.rank_percentile = None
            continue

        vs_avg = p.annualized_vol / avg_vol if avg_vol > 0 else 0.0
        p.vs_average = vs_avg

        rank = sum(1 for v in sorted_vols if v < p.annualized_vol)
        p.rank_percentile = (rank / n) * 100.0 if n > 0 else 0.0

        if vs_avg < 0.5:
            p.volatility_label = "low"
        elif vs_avg < 1.5:
            p.volatility_label = "normal"
        elif vs_avg < 2.5:
            p.volatility_label = "high"
        else:
            p.volatility_label = "extreme"

    return profiles


def profile_to_dict(p: VolatilityProfile) -> dict[str, Any]:
    return {
        "symbol": p.symbol,
        "annualized_vol": round(p.annualized_vol, 4),
        "realized_vol_20d": round(p.realized_vol_20d, 4),
        "volatility_label": p.volatility_label,
        "vs_average": round(p.vs_average, 4),
        "rank_percentile": round(p.rank_percentile, 2) if p.rank_percentile is not None else None,
    }
