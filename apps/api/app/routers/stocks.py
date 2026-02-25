"""
Stock profile and options data for quant analysis.
Uses yfinance for quotes, fundamentals, and options. Greeks computed via Black-Scholes.
Alpha Vantage for quote, overview, time series, and technical indicators.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf
from fastapi import APIRouter, HTTPException, Query

from app.services import alphavantage as av

router = APIRouter(prefix="/stocks", tags=["stocks"])

# Quant-relevant keys from yfinance ticker.info (Yahoo Finance)
INFO_KEYS = [
    "symbol",
    "shortName",
    "longName",
    "regularMarketPrice",
    "previousClose",
    "open",
    "dayHigh",
    "dayLow",
    "fiftyTwoWeekHigh",
    "fiftyTwoWeekLow",
    "fiftyDayAverage",
    "twoHundredDayAverage",
    "volume",
    "averageVolume",
    "marketCap",
    "beta",
    "trailingPE",
    "forwardPE",
    "dividendYield",
    "dividendRate",
    "payoutRatio",
    "52WeekChange",
    "averageDailyVolume10Day",
    "currency",
    "exchange",
    "quoteType",
]


def _safe_float(val: Any, default: float | None = None) -> float | None:
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _get_at_extremes(
    ticker: yf.Ticker, symbol: str
) -> dict[str, float | None]:
    """Compute all-time high/low from max historical data."""
    try:
        hist = ticker.history(period="max", auto_adjust=True)
        if hist is None or hist.empty:
            return {"allTimeHigh": None, "allTimeLow": None}
        high = float(hist["High"].max())
        low = float(hist["Low"].min())
        return {"allTimeHigh": high, "allTimeLow": low}
    except Exception:
        return {"allTimeHigh": None, "allTimeLow": None}


@router.get("/{symbol}/info")
def get_stock_info(symbol: str) -> dict[str, Any]:
    """
    Returns comprehensive stock profile for quant analysis:
    - Current and previous pricing
    - Day / 52-week / all-time highs and lows
    - Volume, market cap
    - Beta, P/E, dividend yield
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch {symbol}: {e}") from e

    if not info:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    # Build profile from known keys
    profile: dict[str, Any] = {}
    for key in INFO_KEYS:
        if key in info and info[key] is not None:
            profile[key] = info[key]

    # Add computed fields
    profile["currentPrice"] = _safe_float(
        info.get("regularMarketPrice") or info.get("currentPrice")
    )
    profile["previousClose"] = _safe_float(info.get("previousClose"))
    profile["changeFromPrevious"] = None
    if profile.get("currentPrice") and profile.get("previousClose"):
        profile["changeFromPrevious"] = round(
            profile["currentPrice"] - profile["previousClose"], 4
        )
    if profile.get("previousClose") and profile.get("changeFromPrevious") is not None:
        profile["changePercent"] = round(
            100 * profile["changeFromPrevious"] / profile["previousClose"], 4
        )
    else:
        profile["changePercent"] = None

    # All-time high/low from history
    extremes = _get_at_extremes(ticker, symbol)
    profile.update(extremes)

    profile["fetchedAt"] = datetime.now(timezone.utc).isoformat()

    return profile


@router.get("/{symbol}/options")
def get_stock_options(
    symbol: str,
    expiry: str | None = Query(None, description="Options expiry date YYYY-MM-DD"),
) -> dict[str, Any]:
    """
    Returns options chain for the symbol with optional Greeks.
    If expiry is omitted, returns nearest expiry dates.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch options: {e}") from e

    if not expirations:
        return {
            "symbol": symbol,
            "expirations": [],
            "expiry": None,
            "calls": [],
            "puts": [],
            "message": "No options data available for this symbol",
        }

    # If no expiry specified, use nearest
    if expiry:
        if expiry not in expirations:
            raise HTTPException(
                status_code=400,
                detail=f"Expiry {expiry} not found. Available: {expirations[:5]}",
            )
        chosen_expiry = expiry
    else:
        chosen_expiry = expirations[0]

    try:
        chain = ticker.option_chain(chosen_expiry)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch option chain: {e}") from e

    def _serialize_df(df) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        return df.reset_index().to_dict(orient="records")

    calls = _serialize_df(chain.calls)
    puts = _serialize_df(chain.puts)

    return {
        "symbol": symbol,
        "expirations": list(expirations),
        "expiry": chosen_expiry,
        "calls": calls,
        "puts": puts,
    }


@router.get("/{symbol}/greeks")
def get_stock_greeks(
    symbol: str,
    expiry: str | None = Query(None),
) -> dict[str, Any]:
    """
    Returns ATM (at-the-money) options Greeks for the symbol.
    Uses implied volatility from options chain; Greeks computed via Black-Scholes.
    Requires py_vollib for Greeks calculation.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    try:
        from py_vollib.black_scholes.greeks.analytical import (
            delta,
            gamma,
            theta,
            vega,
        )
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Greeks require py_vollib. Install with: pip install py_vollib",
        ) from None

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        current_price = _safe_float(info.get("regularMarketPrice") or info.get("currentPrice"))
        if not current_price:
            raise HTTPException(status_code=404, detail=f"No price for {symbol}")

        expirations = ticker.options
        if not expirations:
            raise HTTPException(status_code=404, detail=f"No options for {symbol}")

        chosen_expiry = expiry if expiry and expiry in expirations else expirations[0]
        chain = ticker.option_chain(chosen_expiry)

        # Find ATM call and put (strike closest to current price)
        if chain.calls is None or chain.calls.empty:
            raise HTTPException(status_code=404, detail="No options chain data")

        strikes = chain.calls["strike"].tolist()
        atm_strike = min(strikes, key=lambda k: abs(k - current_price))
        atm_call = chain.calls[chain.calls["strike"] == atm_strike].iloc[0]
        atm_put = chain.puts[chain.puts["strike"] == atm_strike].iloc[0]

        # Time to expiry in years
        exp_dt = datetime.strptime(chosen_expiry, "%Y-%m-%d")
        now = datetime.now(timezone.utc)
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        t = max((exp_dt - now).total_seconds() / (365.25 * 24 * 3600), 1 / 365)

        r = 0.05  # risk-free rate (simplified)
        S, K = current_price, float(atm_strike)
        sigma_call = float(atm_call.get("impliedVolatility", 0.3) or 0.3)
        sigma_put = float(atm_put.get("impliedVolatility", 0.3) or 0.3)
        sigma = (sigma_call + sigma_put) / 2

        def safe_greek(fn, flag, S, K, t, r, sigma):
            try:
                return round(float(fn(flag, S, K, t, r, sigma)), 6)
            except Exception:
                return None

        return {
            "symbol": symbol,
            "expiry": chosen_expiry,
            "underlyingPrice": current_price,
            "atmStrike": atm_strike,
            "timeToExpiryYears": round(t, 4),
            "impliedVolatility": round(sigma, 4),
            "call": {
                "delta": safe_greek(delta, "c", S, K, t, r, sigma),
                "gamma": safe_greek(gamma, "c", S, K, t, r, sigma),
                "theta": safe_greek(theta, "c", S, K, t, r, sigma),
                "vega": safe_greek(vega, "c", S, K, t, r, sigma),
            },
            "put": {
                "delta": safe_greek(delta, "p", S, K, t, r, sigma),
                "gamma": safe_greek(gamma, "p", S, K, t, r, sigma),
                "theta": safe_greek(theta, "p", S, K, t, r, sigma),
                "vega": safe_greek(vega, "p", S, K, t, r, sigma),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greeks failed: {e}") from e


# --- Alpha Vantage endpoints ---


@router.get("/{symbol}/quote")
def get_stock_quote_av(symbol: str) -> dict[str, Any]:
    """
    Latest price and volume from Alpha Vantage (GLOBAL_QUOTE).
    Requires ALPHAVANTAGE_API_KEY in environment.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    try:
        return av.get_global_quote(symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{symbol}/overview")
def get_stock_overview_av(symbol: str) -> dict[str, Any]:
    """
    Company overview and fundamentals from Alpha Vantage (OVERVIEW).
    Requires ALPHAVANTAGE_API_KEY in environment.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    try:
        return av.get_overview(symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{symbol}/timeseries")
def get_stock_timeseries_av(
    symbol: str,
    outputsize: str = Query("compact", description="compact (100 bars) or full (20+ years)"),
) -> dict[str, Any]:
    """
    Daily OHLCV from Alpha Vantage (TIME_SERIES_DAILY).
    Requires ALPHAVANTAGE_API_KEY in environment.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    if outputsize not in ("compact", "full"):
        raise HTTPException(status_code=400, detail="outputsize must be compact or full")
    try:
        bars = av.get_time_series_daily(symbol, outputsize=outputsize)
        return {"symbol": symbol, "bars": bars, "count": len(bars)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{symbol}/rsi")
def get_stock_rsi_av(
    symbol: str,
    time_period: int = Query(14, ge=1, le=100),
    interval: str = Query("daily"),
) -> dict[str, Any]:
    """
    RSI (Relative Strength Index) from Alpha Vantage.
    Requires ALPHAVANTAGE_API_KEY in environment.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    try:
        rows = av.get_rsi(symbol, interval=interval, time_period=time_period)
        return {"symbol": symbol, "rsi": rows, "count": len(rows)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{symbol}/sma")
def get_stock_sma_av(
    symbol: str,
    time_period: int = Query(20, ge=1, le=200),
    interval: str = Query("daily"),
) -> dict[str, Any]:
    """
    Simple Moving Average from Alpha Vantage.
    Requires ALPHAVANTAGE_API_KEY in environment.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    try:
        rows = av.get_sma(symbol, interval=interval, time_period=time_period)
        return {"symbol": symbol, "sma": rows, "count": len(rows)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
