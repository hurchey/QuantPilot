"""
Alpha Vantage API client for stock data.
Docs: https://www.alphavantage.co/documentation/
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from app.config import settings

BASE_URL = "https://www.alphavantage.co/query"


def _get_params(**kwargs: str) -> dict[str, str]:
    params = {"apikey": settings.alphavantage_api_key, **kwargs}
    return {k: v for k, v in params.items() if v}


def _request(function: str, **params: str) -> dict[str, Any]:
    if not settings.alphavantage_api_key:
        raise ValueError("ALPHAVANTAGE_API_KEY is not set")
    p = _get_params(function=function, **params)
    r = requests.get(BASE_URL, params=p, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "Error Message" in data:
        raise ValueError(data["Error Message"])
    if "Note" in data:
        raise ValueError(data["Note"])  # Rate limit message
    return data


def get_global_quote(symbol: str) -> dict[str, Any]:
    """Latest price and volume (GLOBAL_QUOTE)."""
    data = _request("GLOBAL_QUOTE", symbol=symbol)
    quote = data.get("Global Quote", {})
    if not quote:
        return {"symbol": symbol, "message": "No quote data"}
    return {
        "symbol": quote.get("01. symbol", symbol),
        "price": _safe_float(quote.get("05. price")),
        "change": _safe_float(quote.get("09. change")),
        "changePercent": _safe_float(quote.get("10. change percent")),
        "volume": _safe_int(quote.get("06. volume")),
        "open": _safe_float(quote.get("02. open")),
        "high": _safe_float(quote.get("03. high")),
        "low": _safe_float(quote.get("04. low")),
        "previousClose": _safe_float(quote.get("08. previous close")),
        "latestTradingDay": quote.get("07. latest trading day"),
    }


def get_overview(symbol: str) -> dict[str, Any]:
    """Company overview and fundamentals (OVERVIEW)."""
    data = _request("OVERVIEW", symbol=symbol)
    if not data or "Symbol" not in data:
        return {"symbol": symbol, "message": "No overview data"}
    return data


def get_time_series_daily(
    symbol: str,
    outputsize: str = "compact",
) -> list[dict[str, Any]]:
    """
    Daily OHLCV (TIME_SERIES_DAILY).
    outputsize: 'compact' (100) or 'full' (20+ years).
    Returns list of bars sorted by date ascending.
    """
    data = _request("TIME_SERIES_DAILY", symbol=symbol, outputsize=outputsize)
    ts_key = "Time Series (Daily)"
    if ts_key not in data:
        return []
    rows = []
    for date_str, vals in data[ts_key].items():
        try:
            ts = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        rows.append({
            "timestamp": ts.isoformat(),
            "date": date_str,
            "open": _safe_float(vals.get("1. open")),
            "high": _safe_float(vals.get("2. high")),
            "low": _safe_float(vals.get("3. low")),
            "close": _safe_float(vals.get("4. close")),
            "volume": _safe_int(vals.get("5. volume")),
        })
    rows.sort(key=lambda r: r["date"])
    return rows


def get_rsi(
    symbol: str,
    interval: str = "daily",
    time_period: int = 14,
    series_type: str = "close",
) -> list[dict[str, Any]]:
    """RSI (Relative Strength Index) values."""
    data = _request(
        "RSI",
        symbol=symbol,
        interval=interval,
        time_period=str(time_period),
        series_type=series_type,
    )
    key = "Technical Analysis: RSI"
    if key not in data:
        return []
    rows = []
    for date_str, vals in data[key].items():
        rows.append({
            "timestamp": date_str,
            "rsi": _safe_float(vals.get("RSI")),
        })
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def get_sma(
    symbol: str,
    interval: str = "daily",
    time_period: int = 20,
    series_type: str = "close",
) -> list[dict[str, Any]]:
    """Simple Moving Average."""
    data = _request(
        "SMA",
        symbol=symbol,
        interval=interval,
        time_period=str(time_period),
        series_type=series_type,
    )
    key = "Technical Analysis: SMA"
    if key not in data:
        return []
    rows = []
    for date_str, vals in data[key].items():
        rows.append({
            "timestamp": date_str,
            "sma": _safe_float(vals.get("SMA")),
        })
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None
