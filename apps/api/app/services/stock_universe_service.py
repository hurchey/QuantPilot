"""
Stock universe and multi-timeframe data service for backtesting.

Uses Alpha Vantage for:
- LISTING_STATUS: survivorship-bias-free symbol universe
- Daily, weekly, monthly, intraday OHLCV

Rate limits: free tier ~5 calls/min, 500/day. Batch with care.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..models import MarketBar
from . import alphavantage as av


# Alpha Vantage timeframe -> (function, output_key)
TIMEFRAME_MAP = {
    "1d": ("daily", "compact"),
    "1d_full": ("daily", "full"),
    "1w": ("weekly", None),
    "1M": ("monthly", None),
    "1min": ("intraday", "1min"),
    "5min": ("intraday", "5min"),
    "15min": ("intraday", "15min"),
    "30min": ("intraday", "30min"),
    "60min": ("intraday", "60min"),
}


def get_active_symbols(
    date: str | None = None,
    asset_types: tuple[str, ...] = ("Stock", "ETF"),
) -> list[str]:
    """
    Fetch active US symbols from Alpha Vantage LISTING_STATUS.
    Survivorship-bias-free: use date for historical universe.
    """
    rows = av.get_listing_status(date=date, state="active")
    symbols = []
    for r in rows:
        at = (r.get("assetType") or "").strip()
        if not asset_types or at in asset_types:
            sym = (r.get("symbol") or "").strip()
            if sym and len(sym) <= 10:  # filter odd symbols
                symbols.append(sym)
    return sorted(set(symbols))


def fetch_bars_for_symbol(
    symbol: str,
    timeframe: str,
    outputsize: str = "compact",
    month: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch OHLCV bars for one symbol at given timeframe from Alpha Vantage.
    timeframe: 1d, 1d_full, 1w, 1M, 1min, 5min, 15min, 30min, 60min
    """
    symbol = symbol.strip().upper()
    tf = timeframe.strip()

    if tf in ("1d", "1d_full"):
        outsize = "full" if tf == "1d_full" else outputsize
        bars = av.get_time_series_daily(symbol, outputsize=outsize)
    elif tf == "1w":
        bars = av.get_time_series_weekly(symbol)
    elif tf == "1M":
        bars = av.get_time_series_monthly(symbol)
    elif tf in av.INTRADAY_INTERVALS:
        bars = av.get_time_series_intraday(
            symbol,
            interval=tf,
            outputsize=outputsize,
            month=month,
        )
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    return bars


def bars_to_market_bar_rows(
    bars: list[dict[str, Any]],
    symbol: str,
    timeframe: str,
    workspace_id: int,
) -> list[dict[str, Any]]:
    """Convert Alpha Vantage bars to MarketBar insert dicts."""
    rows = []
    for b in bars:
        ts_str = b.get("date") or b.get("timestamp", "")
        try:
            if " " in str(ts_str):
                ts = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
            else:
                ts = datetime.strptime(ts_str[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            continue
        ts = ts.replace(tzinfo=None)
        o = float(b.get("open") or 0)
        h = float(b.get("high") or 0)
        l_ = float(b.get("low") or 0)
        c = float(b.get("close") or 0)
        v = float(b.get("volume") or 0)
        if c <= 0:
            continue
        rows.append({
            "workspace_id": workspace_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": ts,
            "open": o,
            "high": h,
            "low": l_,
            "close": c,
            "volume": v,
        })
    return rows


def fetch_and_store_symbol(
    db: Session,
    *,
    workspace_id: int,
    symbol: str,
    timeframe: str = "1d",
    outputsize: str = "compact",
    rate_limit_delay: float = 12.5,
) -> dict[str, Any]:
    """
    Fetch bars from Alpha Vantage and upsert into MarketBar.
    rate_limit_delay: seconds between API calls (5/min = 12s).
    """
    bars = fetch_bars_for_symbol(symbol, timeframe, outputsize=outputsize)
    if not bars:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "rows_inserted": 0,
            "message": "No data returned",
        }

    rows = bars_to_market_bar_rows(bars, symbol, timeframe, workspace_id)

    existing = {
        r[0]
        for r in db.query(MarketBar.timestamp)
        .filter(
            MarketBar.workspace_id == workspace_id,
            MarketBar.symbol == symbol,
            MarketBar.timeframe == timeframe,
        )
        .all()
    }

    to_insert = [r for r in rows if r["timestamp"] not in existing]
    for r in to_insert:
        db.add(MarketBar(**r))
    db.commit()

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "rows_fetched": len(bars),
        "rows_inserted": len(to_insert),
        "rows_skipped_duplicates": len(rows) - len(to_insert),
    }


def fetch_and_store_batch(
    db: Session,
    *,
    workspace_id: int,
    symbols: list[str],
    timeframe: str = "1d",
    outputsize: str = "compact",
    rate_limit_delay: float = 12.5,
    max_symbols: int | None = 50,
) -> dict[str, Any]:
    """
    Batch fetch and store for multiple symbols.
    Respects Alpha Vantage rate limits (5/min free tier).
    """
    symbols = [s.strip().upper() for s in symbols if s.strip()][: (max_symbols or 999)]
    results = []
    for i, sym in enumerate(symbols):
        if i > 0:
            time.sleep(rate_limit_delay)
        try:
            r = fetch_and_store_symbol(
                db,
                workspace_id=workspace_id,
                symbol=sym,
                timeframe=timeframe,
                outputsize=outputsize,
            )
            results.append(r)
        except Exception as e:
            results.append({
                "symbol": sym,
                "timeframe": timeframe,
                "rows_inserted": 0,
                "error": str(e),
            })
    total_inserted = sum(r.get("rows_inserted", 0) for r in results)
    return {
        "symbols_requested": len(symbols),
        "total_rows_inserted": total_inserted,
        "results": results,
    }
