"""
Regime detection and model switching.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .types import Bar


@dataclass(slots=True)
class RegimeState:
    """Detected market regime."""

    regime: str  # "trending" | "mean_reverting" | "high_vol" | "low_vol"
    confidence: float
    params: dict[str, Any]


def hurst_exponent(returns: list[float], max_lag: int = 20) -> float:
    """
    Hurst exponent H. H < 0.5: mean reverting, H > 0.5: trending.
    Simplified R/S rescaled range.
    """
    n = len(returns)
    if n < max_lag * 2:
        return 0.5
    from math import log, sqrt
    rs_vals = []
    for lag in range(2, min(max_lag, n // 2)):
        k = n // lag
        if k < 2:
            continue
        r_s_list = []
        for i in range(k):
            chunk = returns[i * lag : (i + 1) * lag]
            mean_c = sum(chunk) / len(chunk)
            cumdev = [chunk[j] - mean_c for j in range(len(chunk))]
            cumsum = [sum(cumdev[:j + 1]) for j in range(len(cumdev))]
            R = max(cumsum) - min(cumsum)
            S = (sum((x - mean_c) ** 2 for x in chunk) / len(chunk)) ** 0.5
            if S > 1e-12:
                r_s_list.append(R / S)
        if r_s_list:
            rs_vals.append((lag, sum(r_s_list) / len(r_s_list)))
    if len(rs_vals) < 2:
        return 0.5
    # log(R/S) vs log(lag), slope = H
    log_rs = [log(r) for _, r in rs_vals]
    log_lag = [log(l) for l, _ in rs_vals]
    mean_l = sum(log_lag) / len(log_lag)
    mean_r = sum(log_rs) / len(log_rs)
    num = sum((log_lag[i] - mean_l) * (log_rs[i] - mean_r) for i in range(len(rs_vals)))
    den = sum((log_lag[i] - mean_l) ** 2 for i in range(len(rs_vals)))
    H = num / den if den > 1e-12 else 0.5
    return max(0.0, min(1.0, H))


def rolling_vol_regime(
    returns: list[float],
    window: int = 20,
    high_vol_pct: float = 75,
    low_vol_pct: float = 25,
) -> RegimeState:
    """
    Regime from rolling volatility percentile.
    """
    if len(returns) < window:
        return RegimeState(regime="unknown", confidence=0.0, params={})
    recent = returns[-window:]
    vol = (sum((r - sum(recent) / len(recent)) ** 2 for r in recent) / (len(recent) - 1)) ** 0.5
    # Simplified: compare to own history
    all_vols = []
    for i in range(window, len(returns)):
        chunk = returns[i - window : i]
        m = sum(chunk) / len(chunk)
        v = (sum((x - m) ** 2 for x in chunk) / (len(chunk) - 1)) ** 0.5
        all_vols.append(v)
    if not all_vols:
        return RegimeState(regime="unknown", confidence=0.0, params={"vol": vol})
    sorted_v = sorted(all_vols)
    idx = sum(1 for v in sorted_v if v < vol)
    pct = 100 * idx / len(sorted_v)
    if pct >= high_vol_pct:
        regime = "high_vol"
        conf = (pct - high_vol_pct) / (100 - high_vol_pct)
    elif pct <= low_vol_pct:
        regime = "low_vol"
        conf = (low_vol_pct - pct) / low_vol_pct
    else:
        regime = "normal"
        conf = 0.5
    return RegimeState(regime=regime, confidence=min(1.0, conf), params={"vol": vol, "percentile": pct})


def detect_regime(bars: list[Bar], window: int = 20) -> RegimeState:
    """
    Combined regime: Hurst + vol.
    """
    if len(bars) < window + 2:
        return RegimeState(regime="unknown", confidence=0.0, params={})
    returns = [(bars[i].close / bars[i - 1].close - 1.0) for i in range(1, len(bars))]
    H = hurst_exponent(returns, max_lag=min(20, len(returns) // 2))
    vol_state = rolling_vol_regime(returns, window)
    if H < 0.45:
        regime = "mean_reverting"
        conf = 0.5 + (0.5 - H)
    elif H > 0.55:
        regime = "trending"
        conf = H - 0.5
    else:
        regime = vol_state.regime
        conf = vol_state.confidence
    return RegimeState(
        regime=regime,
        confidence=min(1.0, conf),
        params={"hurst": H, **vol_state.params},
    )
