"""
IV (Implied Volatility) solver for European options.
Uses Newton-Raphson with bisection fallback.
"""

from __future__ import annotations

import math
from typing import Literal

# Small epsilon to avoid div by zero
_EPS = 1e-12
_MAX_ITER = 100
_VOL_TOL = 1e-8


def _norm_cdf(x: float) -> float:
    """Standard normal CDF using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black_scholes_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
) -> float:
    """
    Black-Scholes option price.
    S: spot, K: strike, T: time to expiry (years), r: risk-free rate, sigma: vol.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    d2 = d1 - sigma * sqrt_t
    if option_type == "call":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def vega_bs(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Vega (dPrice/dSigma) for Black-Scholes. Always positive."""
    if T <= 0 or sigma <= 0:
        return 0.0
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    return S * _norm_pdf(d1) * sqrt_t / 100.0  # per 1% vol change


def implied_volatility(
    S: float,
    K: float,
    T: float,
    r: float,
    market_price: float,
    option_type: Literal["call", "put"] = "call",
    precision: float = _VOL_TOL,
) -> float | None:
    """
    Solve for implied volatility given market price.
    Returns sigma (decimal, e.g. 0.25 for 25%) or None if no solution.
    Uses Newton-Raphson with bisection fallback.
    """
    if market_price <= 0 or S <= 0 or K <= 0 or T <= 0:
        return None

    def objective(sig: float) -> float:
        return black_scholes_price(S, K, T, r, sig, option_type) - market_price

    # Bounds: vol between 0.1% and 500%
    vol_low, vol_high = 0.001, 5.0
    price_low = black_scholes_price(S, K, T, r, vol_low, option_type)
    price_high = black_scholes_price(S, K, T, r, vol_high, option_type)

    if market_price < price_low - precision or market_price > price_high + precision:
        return None

    # Newton-Raphson
    sigma = 0.3  # initial guess
    for _ in range(_MAX_ITER):
        price = black_scholes_price(S, K, T, r, sigma, option_type)
        diff = price - market_price
        if abs(diff) < precision:
            return sigma
        v = vega_bs(S, K, T, r, sigma)
        if v < 1e-15:
            break
        sigma = sigma - diff / v
        sigma = max(vol_low, min(vol_high, sigma))

    # Bisection fallback
    low, high = vol_low, vol_high
    for _ in range(_MAX_ITER):
        mid = (low + high) / 2
        if abs(high - low) < precision:
            return mid
        f_mid = objective(mid)
        if abs(f_mid) < precision:
            return mid
        if f_mid > 0:
            high = mid
        else:
            low = mid

    return (low + high) / 2
