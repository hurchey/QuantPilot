"""
Risk-free rate service for options pricing.
Uses config default or DB-stored rates.
"""

from __future__ import annotations

from datetime import datetime, date, timezone

from sqlalchemy.orm import Session

from ..config import settings
from ..models import RiskFreeRate


def get_risk_free_rate(
    db: Session,
    as_of: date | datetime | None = None,
) -> float:
    """
    Get risk-free rate for a given date.
    Prefers DB; falls back to config default.
    """
    if as_of is None:
        as_of = date.today()
    elif isinstance(as_of, datetime):
        as_of = as_of.date()

    dt = datetime(as_of.year, as_of.month, as_of.day, tzinfo=timezone.utc)
    row = (
        db.query(RiskFreeRate)
        .filter(RiskFreeRate.rate_date <= dt)
        .order_by(RiskFreeRate.rate_date.desc())
        .first()
    )
    if row:
        return float(row.rate)
    return settings.default_risk_free_rate


def set_risk_free_rate(
    db: Session,
    rate_date: date | datetime,
    rate: float,
    source: str = "manual",
) -> RiskFreeRate:
    """Store or update a risk-free rate for a date."""
    if isinstance(rate_date, datetime):
        rate_date = rate_date.date()
    dt = datetime(rate_date.year, rate_date.month, rate_date.day, tzinfo=timezone.utc)

    existing = db.query(RiskFreeRate).filter(RiskFreeRate.rate_date == dt).first()
    if existing:
        existing.rate = rate
        existing.source = source
        db.commit()
        db.refresh(existing)
        return existing

    row = RiskFreeRate(rate_date=dt, rate=rate, source=source)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_rates(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
) -> list[dict]:
    """List stored risk-free rates."""
    q = db.query(RiskFreeRate).order_by(RiskFreeRate.rate_date.desc())
    if start_date:
        dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
        q = q.filter(RiskFreeRate.rate_date >= dt)
    if end_date:
        dt = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc)
        q = q.filter(RiskFreeRate.rate_date <= dt)
    rows = q.limit(limit).all()
    return [
        {"date": r.rate_date.strftime("%Y-%m-%d"), "rate": r.rate, "source": r.source}
        for r in rows
    ]
