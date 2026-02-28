"""
Options data service for Phase A + B: fetch chain, persist snapshots, IV + Greeks.

Data sources (in order of preference):
1. Market Data API (marketdata.app) - reliable bid/ask for calls and puts.
   Set MARKETDATA_API_KEY to enable. Free tier: 100 req/day.
2. yfinance (Yahoo Finance) - fallback; bid/ask often missing for illiquid options.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf
from sqlalchemy.orm import Session

from ..models import OptionChainSnapshot
from ..quant.greeks import compute_all_greeks
from ..quant.iv_solver import implied_volatility

try:
    from . import marketdata as md
    _MARKETDATA_AVAILABLE = md.is_available()
except Exception:
    _MARKETDATA_AVAILABLE = False


def _safe_float(val: Any, default: float | None = None) -> float | None:
    if val is None or (isinstance(val, float) and (val != val)):  # NaN
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def fetch_option_chain(symbol: str, expiry: str | None = None) -> dict[str, Any]:
    """
    Fetch option chain (live, not persisted).
    Uses Market Data API if MARKETDATA_API_KEY is set (reliable bid/ask);
    otherwise falls back to yfinance (bid/ask often missing for illiquid options).
    Returns dict with symbol, expirations, expiry, calls, puts.
    """
    symbol = symbol.strip().upper()

    # Prefer Market Data API for reliable bid/ask
    if _MARKETDATA_AVAILABLE:
        try:
            return md.fetch_option_chain(symbol, expiry)
        except Exception:
            pass  # fallback to yfinance

    # Fallback: yfinance
    ticker = yf.Ticker(symbol)
    expirations = ticker.options

    if not expirations:
        return {
            "symbol": symbol,
            "expirations": [],
            "expiry": None,
            "calls": [],
            "puts": [],
            "underlying_price": None,
        }

    chosen_expiry = expiry if expiry and expiry in expirations else expirations[0]
    chain = ticker.option_chain(chosen_expiry)

    info = ticker.info
    underlying_price = _safe_float(info.get("regularMarketPrice") or info.get("currentPrice"))

    def _serialize_df(df) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        rows = []
        for _, row in df.iterrows():
            strike = _safe_float(row.get("strike"), 0)
            bid = _safe_float(row.get("bid"))
            ask = _safe_float(row.get("ask"))
            last = _safe_float(row.get("last")) or _safe_float(row.get("lastPrice"))
            vol = _safe_float(row.get("volume"), 0)
            oi = _safe_float(row.get("openInterest"), 0)
            iv = _safe_float(row.get("impliedVolatility"))
            if last is not None:
                if (bid is None or bid == 0) and (ask is None or (ask is not None and ask <= 0.02)):
                    bid, ask = last, last
                elif bid is None or bid == 0:
                    bid = last
                elif ask is None or ask == 0:
                    ask = last
            rows.append({
                "strike": strike,
                "bid": bid,
                "ask": ask,
                "last": last,
                "volume": vol,
                "openInterest": oi,
                "impliedVolatility": iv,
            })
        return rows

    return {
        "symbol": symbol,
        "expirations": list(expirations),
        "expiry": chosen_expiry,
        "calls": _serialize_df(chain.calls),
        "puts": _serialize_df(chain.puts),
        "underlying_price": underlying_price,
    }


def _time_to_expiry_years(expiry_str: str) -> float:
    """Time to expiry in years."""
    exp_dt = datetime.strptime(expiry_str, "%Y-%m-%d")
    now = datetime.now(timezone.utc)
    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
    secs = max((exp_dt - now).total_seconds(), 86400)  # min 1 day
    return secs / (365.25 * 24 * 3600)


def _enrich_option_with_greeks(
    row: dict[str, Any],
    S: float,
    T: float,
    r: float,
    option_type: str,
) -> dict[str, Any]:
    """Add IV (if missing) and Greeks to an option row."""
    K = _safe_float(row.get("strike"), 0)
    if K <= 0:
        return row
    mid = _safe_float(row.get("bid")) or _safe_float(row.get("ask")) or _safe_float(row.get("last"))
    sigma = _safe_float(row.get("impliedVolatility"))
    opt = "call" if option_type.lower() == "call" else "put"
    if sigma is None and mid is not None and mid > 0:
        sigma = implied_volatility(S, K, T, r, mid, opt)
    if sigma is None:
        sigma = 0.3
    greeks = compute_all_greeks(S, K, T, r, sigma, option_type)
    out = dict(row)
    out["impliedVolatility"] = sigma
    out["greeks"] = greeks
    return out


def fetch_option_chain_with_greeks(
    symbol: str,
    expiry: str | None = None,
    risk_free_rate: float = 0.05,
) -> dict[str, Any]:
    """
    Fetch option chain and compute IV + Greeks for each option (Phase B).
    Uses market IV when available; otherwise solves from mid price.
    """
    data = fetch_option_chain(symbol, expiry)
    if not data["calls"] and not data["puts"]:
        return data
    S = _safe_float(data.get("underlying_price"), 0)
    if S <= 0:
        return data
    T = _time_to_expiry_years(data["expiry"])
    r = risk_free_rate
    data["calls"] = [
        _enrich_option_with_greeks(row, S, T, r, "call")
        for row in data["calls"]
    ]
    data["puts"] = [
        _enrich_option_with_greeks(row, S, T, r, "put")
        for row in data["puts"]
    ]
    return data


def compute_greeks_for_option(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float | None = None,
    market_price: float | None = None,
    option_type: str = "call",
) -> dict[str, Any]:
    """
    Compute Greeks for a single option. Uses sigma if provided; else solves from market_price.
    """
    opt = "call" if option_type.lower() == "call" else "put"
    if sigma is None and market_price is not None and market_price > 0:
        sigma = implied_volatility(S, K, T, r, market_price, opt)
    if sigma is None:
        sigma = 0.3
    greeks = compute_all_greeks(S, K, T, r, sigma, opt)
    return {"impliedVolatility": sigma, "greeks": greeks}


def persist_option_chain_snapshot(
    db: Session,
    workspace_id: int,
    symbol: str,
    expiry: str | None = None,
    snapshot_at: datetime | None = None,
) -> dict[str, Any]:
    """
    Fetch option chain from yfinance and persist to OptionChainSnapshot.
    Returns summary of what was stored.
    """
    symbol = symbol.strip().upper()
    data = fetch_option_chain(symbol, expiry)

    if not data["expirations"]:
        return {
            "symbol": symbol,
            "snapshot_at": None,
            "stored": 0,
            "message": "No options data available for this symbol",
        }

    if snapshot_at is None:
        snapshot_at = datetime.now(timezone.utc).replace(tzinfo=None)

    exp_dt = datetime.strptime(data["expiry"], "%Y-%m-%d").replace(tzinfo=None)

    # Remove existing snapshot for this workspace/symbol/snapshot_at/expiry
    db.query(OptionChainSnapshot).filter(
        OptionChainSnapshot.workspace_id == workspace_id,
        OptionChainSnapshot.symbol == symbol,
        OptionChainSnapshot.snapshot_at == snapshot_at,
        OptionChainSnapshot.expiry == exp_dt,
    ).delete()

    stored = 0
    for row in data["calls"]:
        strike = row.get("strike")
        if strike is None:
            continue
        snap = OptionChainSnapshot(
            workspace_id=workspace_id,
            symbol=symbol,
            snapshot_at=snapshot_at,
            expiry=exp_dt,
            option_type="call",
            strike=float(strike),
            bid=_safe_float(row.get("bid")),
            ask=_safe_float(row.get("ask")),
            last=_safe_float(row.get("last")),
            volume=_safe_float(row.get("volume"), 0),
            open_interest=_safe_float(row.get("openInterest"), 0),
            implied_volatility=_safe_float(row.get("impliedVolatility")),
        )
        db.add(snap)
        stored += 1

    for row in data["puts"]:
        strike = row.get("strike")
        if strike is None:
            continue
        snap = OptionChainSnapshot(
            workspace_id=workspace_id,
            symbol=symbol,
            snapshot_at=snapshot_at,
            expiry=exp_dt,
            option_type="put",
            strike=float(strike),
            bid=_safe_float(row.get("bid")),
            ask=_safe_float(row.get("ask")),
            last=_safe_float(row.get("last")),
            volume=_safe_float(row.get("volume"), 0),
            open_interest=_safe_float(row.get("openInterest"), 0),
            implied_volatility=_safe_float(row.get("impliedVolatility")),
        )
        db.add(snap)
        stored += 1

    db.commit()

    return {
        "symbol": symbol,
        "snapshot_at": snapshot_at.isoformat(),
        "expiry": data["expiry"],
        "stored": stored,
        "calls": len(data["calls"]),
        "puts": len(data["puts"]),
    }


def list_snapshots(
    db: Session,
    workspace_id: int,
    symbol: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List stored option chain snapshots for a workspace.
    """
    q = (
        db.query(OptionChainSnapshot.symbol, OptionChainSnapshot.snapshot_at, OptionChainSnapshot.expiry)
        .filter(OptionChainSnapshot.workspace_id == workspace_id)
        .distinct()
    )
    if symbol:
        q = q.filter(OptionChainSnapshot.symbol == symbol.strip().upper())
    q = q.order_by(OptionChainSnapshot.snapshot_at.desc()).limit(limit)

    rows = q.all()
    seen: set[tuple[str, datetime, datetime]] = set()
    result = []
    for r in rows:
        key = (r.symbol, r.snapshot_at, r.expiry)
        if key not in seen:
            seen.add(key)
            result.append({
                "symbol": r.symbol,
                "snapshot_at": r.snapshot_at.isoformat() if r.snapshot_at else None,
                "expiry": r.expiry.strftime("%Y-%m-%d") if r.expiry else None,
            })
    return result


def get_snapshot_chain(
    db: Session,
    workspace_id: int,
    symbol: str,
    snapshot_at: datetime,
    expiry: datetime | None = None,
) -> dict[str, Any]:
    """
    Retrieve a stored option chain snapshot.
    """
    symbol = symbol.strip().upper()
    q = (
        db.query(OptionChainSnapshot)
        .filter(OptionChainSnapshot.workspace_id == workspace_id)
        .filter(OptionChainSnapshot.symbol == symbol)
        .filter(OptionChainSnapshot.snapshot_at == snapshot_at)
    )
    if expiry:
        q = q.filter(OptionChainSnapshot.expiry == expiry)

    rows = q.all()
    calls = []
    puts = []
    for r in rows:
        row = {
            "strike": r.strike,
            "bid": r.bid,
            "ask": r.ask,
            "last": r.last,
            "volume": r.volume,
            "openInterest": r.open_interest,
            "impliedVolatility": r.implied_volatility,
        }
        if r.option_type == "call":
            calls.append(row)
        else:
            puts.append(row)

    calls.sort(key=lambda x: x["strike"])
    puts.sort(key=lambda x: x["strike"])

    return {
        "symbol": symbol,
        "snapshot_at": snapshot_at.isoformat(),
        "expiry": rows[0].expiry.strftime("%Y-%m-%d") if rows else None,
        "calls": calls,
        "puts": puts,
    }
