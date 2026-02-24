from __future__ import annotations


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


def calculate_fee(notional: float, fees_bps: float) -> float:
    if fees_bps <= 0:
        return 0.0
    return float(notional) * (fees_bps / 10_000.0)