"""
Market Data API client for options chain (bid/ask, Greeks).
https://www.marketdata.app/docs/sdk/py/options/chain

Provides reliable bid/ask for both calls and puts. Free tier: 100 req/day.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from app.config import settings

BASE_URL = "https://api.marketdata.app/v1/options/chain"


def _get_token() -> str:
    if not settings.marketdata_api_key:
        raise ValueError("MARKETDATA_API_KEY is not set")
    return settings.marketdata_api_key


def fetch_option_chain(
    symbol: str,
    expiry: str | None = None,
) -> dict[str, Any]:
    """
    Fetch option chain from Market Data API.
    Returns dict with symbol, expirations, expiry, calls, puts, underlying_price.
    Uses same shape as options_service for compatibility.
    """
    symbol = symbol.strip().upper()
    token = _get_token()

    params: dict[str, str] = {"token": token}
    if expiry:
        params["expiration"] = expiry

    url = f"{BASE_URL}/{symbol}"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    if data.get("s") != "ok":
        raise ValueError(data.get("message", "Market Data API error"))

    # Parse parallel arrays
    option_symbols = data.get("optionSymbol", [])
    sides = data.get("side", [])
    strikes = data.get("strike", [])
    bids = data.get("bid", [])
    asks = data.get("ask", [])
    lasts = data.get("last", [])
    volumes = data.get("volume", [])
    open_interests = data.get("openInterest", [])
    ivs = data.get("iv", [])
    underlying_prices = data.get("underlyingPrice", [])
    expirations_ts = data.get("expiration", [])

    def _safe_float(val: Any, default: float | None = None) -> float | None:
        if val is None or (isinstance(val, float) and (val != val)):
            return default
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    # Group by expiry (Unix timestamp -> YYYY-MM-DD)
    expiry_to_options: dict[str, list[dict]] = {}
    for i in range(len(option_symbols)):
        ts = expirations_ts[i] if i < len(expirations_ts) else None
        exp_str = "unknown"
        if ts is not None:
            try:
                dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                exp_str = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        if exp_str not in expiry_to_options:
            expiry_to_options[exp_str] = []

        row = {
            "strike": _safe_float(strikes[i] if i < len(strikes) else None, 0),
            "bid": _safe_float(bids[i] if i < len(bids) else None),
            "ask": _safe_float(asks[i] if i < len(asks) else None),
            "last": _safe_float(lasts[i] if i < len(lasts) else None),
            "volume": _safe_float(volumes[i] if i < len(volumes) else None, 0),
            "openInterest": _safe_float(open_interests[i] if i < len(open_interests) else None, 0),
            "impliedVolatility": _safe_float(ivs[i] if i < len(ivs) else None),
        }
        side = sides[i] if i < len(sides) else "call"
        if side.lower() == "call":
            expiry_to_options[exp_str].append(("call", row))
        else:
            expiry_to_options[exp_str].append(("put", row))

    # Build unique expirations list (sorted)
    all_expirations = sorted(expiry_to_options.keys())
    if not all_expirations:
        return {
            "symbol": symbol,
            "expirations": [],
            "expiry": None,
            "calls": [],
            "puts": [],
            "underlying_price": None,
        }

    # Pick expiry: requested or first available
    chosen_expiry = expiry if expiry and expiry in all_expirations else all_expirations[0]
    opts = expiry_to_options.get(chosen_expiry, [])

    calls = [r for t, r in opts if t == "call"]
    puts = [r for t, r in opts if t == "put"]

    # Sort by strike
    calls.sort(key=lambda x: x["strike"] or 0)
    puts.sort(key=lambda x: x["strike"] or 0)

    # Underlying price from first option if available
    underlying_price = None
    if underlying_prices:
        underlying_price = _safe_float(underlying_prices[0])

    return {
        "symbol": symbol,
        "expirations": all_expirations,
        "expiry": chosen_expiry,
        "calls": calls,
        "puts": puts,
        "underlying_price": underlying_price,
    }


def is_available() -> bool:
    """True if Market Data API key is configured."""
    return bool(settings.marketdata_api_key)
