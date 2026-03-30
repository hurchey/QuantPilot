# apps/api/app/research/scanner.py
"""
Universe scanner: identifies extreme upside dislocations (500%+ 3-day moves)
in U.S.-listed equities using yfinance historical data.
"""
from __future__ import annotations

from typing import Optional

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def _strip_tz(dt) -> datetime:
    """Convert timezone-aware datetime to naive UTC for SQLite compatibility."""
    if dt is None:
        return None
    if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def scan_symbol(
    symbol: str,
    start_date: str = "2010-01-01",
    end_date: Optional[str] = None,
    min_return_3d_pct: float = 100.0,
    min_price: float = 0.50,
    max_events_per_symbol: int = 5,
) -> list[dict]:
    """
    Scan a single symbol for extreme short-horizon returns.

    Checks both 3-day and 1-day returns. An event qualifies if either:
      - 3-day return >= min_return_3d_pct, OR
      - 1-day return >= min_return_3d_pct

    Filters:
      - min_price: skip events where the starting price is below this (filters penny stock noise)
      - max_events_per_symbol: keep only the top N events by return (prevents one ticker dominating)

    Labels are always based on fixed thresholds:
      Label A: best return (max of 1d, 3d) >= 100%
      Label B: best return >= 500%

    Returns a list of dislocation event dicts, one per qualifying window.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date, auto_adjust=True)
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", symbol, e)
        return []

    if hist.empty or len(hist) < 4:
        return []

    # Compute rolling returns
    close = hist["Close"]
    ret_3d = (close / close.shift(3) - 1) * 100  # 3-day percentage return
    ret_1d = (close / close.shift(1) - 1) * 100  # 1-day percentage return

    # Qualify on either 1-day OR 3-day return
    mask = (ret_3d >= min_return_3d_pct) | (ret_1d >= min_return_3d_pct)
    if not mask.any():
        return []

    events = []
    qualifying_dates = ret_3d[mask].index.tolist()

    # Cluster nearby events (within 5 trading days) and keep the peak
    clusters: list[list] = []
    current_cluster: list = [qualifying_dates[0]]
    for i in range(1, len(qualifying_dates)):
        if (qualifying_dates[i] - qualifying_dates[i - 1]).days <= 7:
            current_cluster.append(qualifying_dates[i])
        else:
            clusters.append(current_cluster)
            current_cluster = [qualifying_dates[i]]
    clusters.append(current_cluster)

    for cluster in clusters:
        # Pick the date with the highest 3-day return in the cluster
        best_date = max(cluster, key=lambda d: ret_3d.loc[d])
        best_idx = hist.index.get_loc(best_date)

        # Event window: 3 trading days back from best_date
        start_idx = max(0, best_idx - 3)
        event_start = hist.index[start_idx]

        # Price data
        price_start = float(close.iloc[start_idx])
        price_peak = float(hist["High"].iloc[start_idx : best_idx + 1].max())
        price_end_3d = float(close.loc[best_date])

        return_3d_val = float(ret_3d.loc[best_date])
        return_1d_val = float(ret_1d.loc[best_date]) if best_date in ret_1d.index else None

        # Peak return (intraday high vs start close)
        return_peak = ((price_peak / price_start) - 1) * 100 if price_start > 0 else None

        # Best return for labeling (use whichever is higher)
        best_return = max(return_3d_val, return_1d_val or 0, return_peak or 0)

        # Day-after continuation
        day_after_cont = None
        if best_idx + 1 < len(hist):
            next_close = float(close.iloc[best_idx + 1])
            day_after_cont = 1 if next_close > price_end_3d else 0

        # Volume on event day and 20-day pre-event average
        vol_event = float(hist["Volume"].loc[best_date])
        pre_start = max(0, start_idx - 20)
        vol_avg_20d = float(hist["Volume"].iloc[pre_start:start_idx].mean()) if start_idx > 0 else None
        vol_ratio = (vol_event / vol_avg_20d) if vol_avg_20d and vol_avg_20d > 0 else None

        # Peak date (which day in window had the highest high)
        window_slice = hist.iloc[start_idx : best_idx + 1]
        peak_date = window_slice["High"].idxmax()

        # Skip events where starting price is below minimum (penny stock noise)
        if price_start < min_price:
            continue

        event = {
            "symbol": symbol.upper(),
            "event_start_date": _strip_tz(event_start.to_pydatetime()),
            "event_end_date": _strip_tz(best_date.to_pydatetime()),
            "peak_date": _strip_tz(peak_date.to_pydatetime()) if pd.notna(peak_date) else None,
            "price_start": round(price_start, 4),
            "price_peak": round(price_peak, 4),
            "price_end_3d": round(price_end_3d, 4),
            "return_1d_pct": round(return_1d_val, 2) if return_1d_val is not None else None,
            "return_3d_pct": round(return_3d_val, 2),
            "return_peak_pct": round(return_peak, 2) if return_peak is not None else None,
            "label_a": 1 if best_return >= 100.0 else 0,
            "label_b": 1 if best_return >= 500.0 else 0,
            "day_after_continuation": day_after_cont,
            "volume_event_day": vol_event,
            "volume_avg_20d_pre": round(vol_avg_20d, 2) if vol_avg_20d is not None else None,
            "volume_ratio": round(vol_ratio, 2) if vol_ratio is not None else None,
            "data_source": "yfinance",
        }
        events.append(event)

    # Keep only the top N events by return to prevent one ticker from dominating
    if len(events) > max_events_per_symbol:
        events.sort(key=lambda e: e["return_3d_pct"], reverse=True)
        events = events[:max_events_per_symbol]

    return events


def scan_symbols(
    symbols: list[str],
    start_date: str = "2010-01-01",
    end_date: Optional[str] = None,
    min_return_3d_pct: float = 100.0,
) -> tuple[list[dict], list[str]]:
    """
    Scan multiple symbols. Returns (all_events, errors).
    """
    all_events: list[dict] = []
    errors: list[str] = []

    for symbol in symbols:
        try:
            events = scan_symbol(symbol, start_date, end_date, min_return_3d_pct)
            all_events.extend(events)
        except Exception as e:
            msg = f"{symbol}: {e}"
            logger.error("Scan error for %s", msg)
            errors.append(msg)

    return all_events, errors


# --- Predefined universe lists ---


def get_universe_symbols(universe: str) -> list[str]:
    """
    Return a list of ticker symbols for a predefined universe.
    For large universes, this fetches from Wikipedia or static lists.
    """
    if universe == "sp500":
        return _get_sp500_symbols()
    elif universe == "russell2000":
        # Russell 2000 tickers are harder to get freely.
        # Start with a smaller sample or use a static file.
        logger.info("Russell 2000 universe: using S&P 600 small-cap as proxy")
        return _get_sp600_symbols()
    elif universe == "all_us":
        # Combine multiple lists
        symbols = set(_get_sp500_symbols())
        symbols.update(_get_sp600_symbols())
        return sorted(symbols)
    else:
        raise ValueError(f"Unknown universe: {universe}. Use 'sp500', 'russell2000', 'all_us', or 'custom'.")


def _get_sp500_symbols() -> list[str]:
    """Fetch S&P 500 constituent tickers from Wikipedia."""
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = tables[0]
        return sorted(df["Symbol"].str.replace(".", "-", regex=False).tolist())
    except Exception as e:
        logger.error("Failed to fetch S&P 500 list: %s", e)
        return []


def _get_sp600_symbols() -> list[str]:
    """Fetch S&P 600 SmallCap constituent tickers from Wikipedia."""
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_600_companies")
        df = tables[0]
        return sorted(df["Symbol"].str.replace(".", "-", regex=False).tolist())
    except Exception as e:
        logger.error("Failed to fetch S&P 600 list: %s", e)
        return []
