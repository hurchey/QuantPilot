"""
Dividend service for options pricing and corporate actions.
Fetches from yfinance; can persist to DB for backtesting.
"""

from __future__ import annotations

from datetime import datetime, timezone

import yfinance as yf
from sqlalchemy.orm import Session

from ..models import Dividend


def fetch_dividends(symbol: str) -> list[dict]:
    """
    Fetch dividend history from yfinance (live, not persisted).
    Returns list of {date, amount, currency}.
    """
    symbol = symbol.strip().upper()
    ticker = yf.Ticker(symbol)
    hist = ticker.dividends

    if hist is None or hist.empty:
        return []

    result = []
    for dt, amount in hist.items():
        if hasattr(dt, "to_pydatetime"):
            dt = dt.to_pydatetime()
        result.append({
            "date": dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt),
            "amount": float(amount),
            "currency": "USD",
        })
    result.sort(key=lambda x: x["date"], reverse=True)
    return result


def persist_dividends(
    db: Session,
    symbol: str,
    dividends: list[dict],
) -> int:
    """
    Persist dividends to DB. Upserts by (symbol, ex_date).
    Returns count of rows inserted/updated.
    """
    symbol = symbol.strip().upper()
    stored = 0
    for d in dividends:
        date_str = d.get("date")
        amount = d.get("amount")
        if not date_str or amount is None:
            continue
        try:
            ex_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=None)
        except ValueError:
            continue

        existing = (
            db.query(Dividend)
            .filter(Dividend.symbol == symbol, Dividend.ex_date == ex_dt)
            .first()
        )
        if existing:
            existing.amount = float(amount)
            existing.currency = d.get("currency", "USD")
            stored += 1
        else:
            row = Dividend(
                symbol=symbol,
                ex_date=ex_dt,
                amount=float(amount),
                currency=d.get("currency", "USD"),
            )
            db.add(row)
            stored += 1

    db.commit()
    return stored


def get_dividends(
    db: Session,
    symbol: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    """
    Get dividends from DB for a symbol.
    Falls back to yfinance fetch if DB empty.
    """
    symbol = symbol.strip().upper()
    q = db.query(Dividend).filter(Dividend.symbol == symbol)
    if start_date:
        q = q.filter(Dividend.ex_date >= start_date)
    if end_date:
        q = q.filter(Dividend.ex_date <= end_date)
    rows = q.order_by(Dividend.ex_date.desc()).all()

    if rows:
        return [
            {
                "date": r.ex_date.strftime("%Y-%m-%d"),
                "amount": r.amount,
                "currency": r.currency,
            }
            for r in rows
        ]

    # Fallback to live fetch
    return fetch_dividends(symbol)
