"""
Black-Scholes Greeks calculator for European options.
Delta, gamma, theta, vega, rho.
"""

from __future__ import annotations

import math
from typing import Literal

_EPS = 1e-12


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def delta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
) -> float:
    """Delta: dPrice/dSpot."""
    if T <= 0 or sigma <= 0:
        return 0.5 if option_type == "call" else -0.5
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    if option_type == "call":
        return _norm_cdf(d1)
    return _norm_cdf(d1) - 1.0


def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Gamma: d2Price/dSpot2. Same for call and put."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.0
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    return _norm_pdf(d1) / (S * sigma * sqrt_t + _EPS)


def theta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
) -> float:
    """Theta: dPrice/dTime (per year). Negative = time decay."""
    if T <= 0 or sigma <= 0:
        return 0.0
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    d2 = d1 - sigma * sqrt_t
    term1 = -S * _norm_pdf(d1) * sigma / (2 * sqrt_t + _EPS)
    if option_type == "call":
        term2 = -r * K * math.exp(-r * T) * _norm_cdf(d2)
        return (term1 + term2) / 365.0  # per day
    term2 = r * K * math.exp(-r * T) * _norm_cdf(-d2)
    return (term1 + term2) / 365.0


def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Vega: dPrice/dSigma (per 1% vol change). Same for call and put."""
    if T <= 0 or sigma <= 0:
        return 0.0
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    return S * _norm_pdf(d1) * sqrt_t / 100.0


def rho(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
) -> float:
    """Rho: dPrice/dRate (per 1% rate change)."""
    if T <= 0 or sigma <= 0:
        return 0.0
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    d2 = d1 - sigma * sqrt_t
    if option_type == "call":
        return -T * K * math.exp(-r * T) * _norm_cdf(d2) / 100.0
    return T * K * math.exp(-r * T) * _norm_cdf(-d2) / 100.0


def black_scholes_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
) -> float:
    """Black-Scholes option price."""
    if T <= 0 or sigma <= 0:
        return 0.0
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_t + _EPS)
    d2 = d1 - sigma * sqrt_t
    if option_type == "call":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def compute_all_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
) -> dict[str, float]:
    """Compute all Greeks for an option."""
    return {
        "delta": round(delta(S, K, T, r, sigma, option_type), 6),
        "gamma": round(gamma(S, K, T, r, sigma), 6),
        "theta": round(theta(S, K, T, r, sigma, option_type), 6),
        "vega": round(vega(S, K, T, r, sigma), 6),
        "rho": round(rho(S, K, T, r, sigma, option_type), 6),
    }
