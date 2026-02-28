"""
Position sizing: vol targeting, Kelly criterion.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class SizingResult:
    """Position size as fraction of capital."""

    weight: float  # 0-1, fraction of capital
    method: str
    raw_kelly: float | None = None


def kelly_fraction(
    win_prob: float,
    win_loss_ratio: float,
    fraction: float = 1.0,
) -> float:
    """
    Kelly criterion: f* = (p*b - q) / b
    p=win prob, q=1-p, b=win/loss ratio (avg win / avg loss).
    fraction: full Kelly = 1, half Kelly = 0.5.
    """
    if win_loss_ratio <= 0:
        return 0.0
    q = 1.0 - win_prob
    f_star = (win_prob * win_loss_ratio - q) / win_loss_ratio
    f_star = max(0.0, min(f_star, 1.0))
    return f_star * fraction


def vol_target_weight(
    target_vol: float,
    asset_vol: float,
    max_weight: float = 1.0,
) -> float:
    """
    Size position so portfolio vol = target_vol.
    weight = target_vol / asset_vol (clipped to max_weight).
    """
    if asset_vol <= 0:
        return 0.0
    w = target_vol / asset_vol
    return min(w, max_weight)


def position_size(
    method: str,
    win_prob: float = 0.5,
    win_loss_ratio: float = 1.0,
    target_vol: float = 0.15,
    asset_vol: float = 0.2,
    kelly_fraction_pct: float = 0.5,
) -> SizingResult:
    """
    Compute position size by method.
    method: "kelly" | "vol_target" | "fixed"
    """
    if method == "kelly":
        w = kelly_fraction(win_prob, win_loss_ratio, kelly_fraction_pct)
        return SizingResult(weight=w, method="kelly", raw_kelly=w / kelly_fraction_pct if kelly_fraction_pct else None)
    if method == "vol_target":
        w = vol_target_weight(target_vol, asset_vol)
        return SizingResult(weight=w, method="vol_target")
    return SizingResult(weight=1.0, method="fixed")
