"""
Alpha Vantage API client for stock data.
Docs: https://www.alphavantage.co/documentation/

Supports: daily, weekly, monthly, intraday (1min, 5min, 15min, 30min, 60min).
LISTING_STATUS for survivorship-bias-free universe.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

import requests

from app.config import settings

BASE_URL = "https://www.alphavantage.co/query"

# Intraday intervals supported by Alpha Vantage
INTRADAY_INTERVALS = ("1min", "5min", "15min", "30min", "60min")


def _get_params(**kwargs: str) -> dict[str, str]:
    params = {"apikey": settings.alphavantage_api_key, **kwargs}
    return {k: v for k, v in params.items() if v}


def _request(function: str, **params: str) -> dict[str, Any]:
    if not settings.alphavantage_api_key:
        raise ValueError("ALPHAVANTAGE_API_KEY is not set")
    p = _get_params(function=function, **params)
    r = requests.get(BASE_URL, params=p, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "Error Message" in data:
        raise ValueError(data["Error Message"])
    if "Note" in data:
        raise ValueError(data["Note"])  # Rate limit message
    return data


def _request_csv(function: str, **params: str) -> str:
    """Request CSV response (used by LISTING_STATUS)."""
    if not settings.alphavantage_api_key:
        raise ValueError("ALPHAVANTAGE_API_KEY is not set")
    p = _get_params(function=function, datatype="csv", **params)
    r = requests.get(BASE_URL, params=p, timeout=60)
    r.raise_for_status()
    return r.text


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


def get_time_series_weekly(symbol: str) -> list[dict[str, Any]]:
    """
    Weekly OHLCV (TIME_SERIES_WEEKLY). ~20+ years history.
    Returns list of bars sorted by date ascending.
    """
    data = _request("TIME_SERIES_WEEKLY", symbol=symbol)
    ts_key = "Weekly Time Series"
    if ts_key not in data:
        return []
    return _parse_ts_into_rows(data[ts_key], date_fmt="%Y-%m-%d")


def get_time_series_monthly(symbol: str) -> list[dict[str, Any]]:
    """
    Monthly OHLCV (TIME_SERIES_MONTHLY). ~20+ years history.
    Returns list of bars sorted by date ascending.
    """
    data = _request("TIME_SERIES_MONTHLY", symbol=symbol)
    ts_key = "Monthly Time Series"
    if ts_key not in data:
        return []
    return _parse_ts_into_rows(data[ts_key], date_fmt="%Y-%m-%d")


def get_time_series_intraday(
    symbol: str,
    interval: str = "5min",
    outputsize: str = "compact",
    month: str | None = None,
) -> list[dict[str, Any]]:
    """
    Intraday OHLCV (TIME_SERIES_INTRADAY).
    interval: 1min, 5min, 15min, 30min, 60min.
    outputsize: compact (100 bars) or full (30 days or full month).
    month: YYYY-MM for historical month (e.g. "2024-01").
    Note: Intraday is premium on Alpha Vantage; free tier may have limited access.
    """
    if interval not in INTRADAY_INTERVALS:
        raise ValueError(f"interval must be one of {INTRADAY_INTERVALS}")
    params: dict[str, str] = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
    }
    if month:
        params["month"] = month
    data = _request("TIME_SERIES_INTRADAY", **params)
    ts_key = f"Time Series ({interval})"
    if ts_key not in data:
        return []
    return _parse_ts_into_rows(data[ts_key], date_fmt="%Y-%m-%d %H:%M:%S")


def _parse_ts_into_rows(
    ts_dict: dict[str, Any],
    date_fmt: str = "%Y-%m-%d",
) -> list[dict[str, Any]]:
    rows = []
    for date_str, vals in ts_dict.items():
        try:
            ts = datetime.strptime(date_str.strip(), date_fmt)
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


def get_listing_status(
    date: str | None = None,
    state: str = "active",
) -> list[dict[str, Any]]:
    """
    LISTING_STATUS: returns all US symbols (active or delisted).
    Use for survivorship-bias-free universe.
    date: YYYY-MM-DD for historical snapshot; omit for latest.
    state: 'active' or 'delisted'.
    Returns list of dicts with symbol, name, exchange, assetType, etc.
    """
    if not settings.alphavantage_api_key:
        raise ValueError("ALPHAVANTAGE_API_KEY is not set")
    params: dict[str, str] = {"function": "LISTING_STATUS", "state": state}
    if date:
        params["date"] = date
    p = _get_params(**params)
    r = requests.get(BASE_URL, params=p, timeout=30)
    r.raise_for_status()
    text = r.text
    # Response can be JSON or CSV; LISTING_STATUS returns CSV
    if text.strip().startswith("{"):
        data = r.json()
        if "Error Message" in data:
            raise ValueError(data["Error Message"])
        if "Note" in data:
            raise ValueError(data["Note"])
        return []
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    # Normalize: symbol, name, exchange, assetType, ipoDate, delistingDate
    out = []
    for row in rows:
        out.append({
            "symbol": (row.get("symbol") or "").strip(),
            "name": (row.get("name") or "").strip(),
            "exchange": (row.get("exchange") or "").strip(),
            "assetType": (row.get("assetType") or "").strip(),
            "ipoDate": (row.get("ipoDate") or "").strip(),
            "delistingDate": (row.get("delistingDate") or "").strip(),
        })
    return [r for r in out if r["symbol"]]


def get_news_sentiment(
    tickers: str | list[str],
    limit: int = 50,
    time_from: str | None = None,
    time_to: str | None = None,
    sort: str = "LATEST",
) -> list[dict[str, Any]]:
    """
    NEWS_SENTIMENT: news articles with sentiment per ticker.
    tickers: comma-separated string or list, e.g. "AAPL" or ["AAPL","MSFT"]
    limit: max 1000
    time_from/time_to: YYYYMMDDTHHMM format
    Returns list of feed items with ticker_sentiment, relevance_score, etc.
    """
    if isinstance(tickers, list):
        tickers = ",".join(t.strip().upper() for t in tickers)
    params: dict[str, str] = {
        "tickers": tickers,
        "limit": str(min(limit, 1000)),
        "sort": sort,
    }
    if time_from:
        params["time_from"] = time_from
    if time_to:
        params["time_to"] = time_to
    data = _request("NEWS_SENTIMENT", **params)
    feed = data.get("feed", [])
    return feed if isinstance(feed, list) else []


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
