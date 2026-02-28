"""
Cost models for realistic backtesting.

Includes: slippage, fees, bid-ask spread, market impact, borrow costs.
"""

from __future__ import annotations

import math


def apply_slippage(price: float, side: str, slippage_bps: float) -> float:
    """
    Buy pays up, sell receives less.
    """
    price = float(price)
    if slippage_bps <= 0:
        return price

    slip = slippage_bps / 10_000.0
    if side.lower() == "buy":
        return price * (1.0 + slip)
    if side.lower() == "sell":
        return price * (1.0 - slip)
    raise ValueError("side must be 'buy' or 'sell'")


def apply_spread(price: float, side: str, spread_bps: float) -> float:
    """
    Half-spread: buy pays mid + half, sell receives mid - half.
    """
    price = float(price)
    if spread_bps <= 0:
        return price
    half = (spread_bps / 10_000.0) * price / 2.0
    if side.lower() == "buy":
        return price + half
    if side.lower() == "sell":
        return price - half
    raise ValueError("side must be 'buy' or 'sell'")


def market_impact_bps(
    notional: float,
    adv: float,
    impact_coef: float = 0.1,
) -> float:
    """
    Square-root market impact model (Almgren-Chriss style).
    impact_bps ≈ impact_coef * sqrt(notional / adv) * 10000
    adv: average daily volume in dollars
    """
    if adv <= 0 or notional <= 0:
        return 0.0
    participation = notional / adv
    if participation >= 1.0:
        participation = 1.0  # cap at 100%
    impact = impact_coef * math.sqrt(participation)
    return impact * 10_000  # to bps


def apply_market_impact(price: float, side: str, impact_bps: float) -> float:
    """Apply market impact to execution price."""
    if impact_bps <= 0:
        return price
    mult = impact_bps / 10_000.0
    if side.lower() == "buy":
        return price * (1.0 + mult)
    if side.lower() == "sell":
        return price * (1.0 - mult)
    raise ValueError("side must be 'buy' or 'sell'")


def borrow_cost_annual(borrow_rate_bps: float, days_held: float) -> float:
    """
    Borrow cost for short selling (annual rate -> prorated).
    Returns cost as fraction of position value (e.g. 0.001 = 0.1%).
    """
    if borrow_rate_bps <= 0:
        return 0.0
    return (borrow_rate_bps / 10_000.0) * (days_held / 365.0)


def calculate_fee(notional: float, fees_bps: float) -> float:
    if fees_bps <= 0:
        return 0.0
    return float(notional) * (fees_bps / 10_000.0)


def total_execution_price(
    mid_price: float,
    side: str,
    slippage_bps: float,
    spread_bps: float,
    impact_bps: float = 0,
) -> float:
    """
    Combine slippage, spread, and impact into single execution price.
    Order of application: spread -> slippage -> impact.
    """
    p = mid_price
    if spread_bps > 0:
        p = apply_spread(p, side, spread_bps)
    if slippage_bps > 0:
        p = apply_slippage(p, side, slippage_bps)
    if impact_bps > 0:
        p = apply_market_impact(p, side, impact_bps)
    return p