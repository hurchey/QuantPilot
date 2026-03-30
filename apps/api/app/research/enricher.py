# apps/api/app/research/enricher.py
"""
Feature collector: enriches dislocation events with float, short interest,
fundamentals, sector, and structural data from yfinance and other sources.
"""
from __future__ import annotations

from typing import Optional

import logging
from datetime import datetime

import yfinance as yf
from sqlalchemy.orm import Session

from ..models import DislocationEvent, DislocationFeature

logger = logging.getLogger(__name__)


def enrich_event(db: Session, event: DislocationEvent) -> list[str]:
    """
    Enrich a single dislocation event with data from yfinance.
    Returns a list of error messages (empty if all succeeded).
    """
    errors: list[str] = []
    symbol = event.symbol

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
    except Exception as e:
        return [f"{symbol}: failed to fetch info - {e}"]

    # --- Company identity ---
    event.company_name = info.get("longName") or info.get("shortName")
    event.exchange = info.get("exchange")
    event.sector = info.get("sector")
    event.industry = info.get("industry")

    # Security type classification
    event.security_type = _classify_security_type(info, symbol)

    # --- Float & share structure ---
    event.shares_outstanding = info.get("sharesOutstanding")
    event.float_shares = info.get("floatShares")

    # Market cap before event (shares * start price)
    if event.shares_outstanding and event.price_start:
        event.market_cap_pre = event.shares_outstanding * event.price_start

    # --- Short interest ---
    event.short_interest_shares = info.get("sharesShort")
    event.short_pct_float = info.get("shortPercentOfFloat")
    event.days_to_cover = info.get("shortRatio")  # days to cover

    # --- IPO date ---
    ipo_raw = info.get("ipoDate")  # not always available
    if not ipo_raw:
        # Try firstTradeDateEpochUtc
        epoch = info.get("firstTradeDateEpochUtc")
        if epoch:
            try:
                event.ipo_date = datetime.utcfromtimestamp(epoch)
            except (ValueError, OSError):
                pass
    else:
        try:
            event.ipo_date = datetime.strptime(str(ipo_raw), "%Y-%m-%d")
        except ValueError:
            pass

    if event.ipo_date and event.event_start_date:
        event.days_since_ipo = (event.event_start_date - event.ipo_date).days

    # --- Options availability ---
    try:
        expirations = ticker.options
        event.options_available = 1 if expirations else 0
    except Exception:
        event.options_available = None

    # --- Store additional features in the flexible feature table ---
    _store_feature(db, event.id, "country", info.get("country"))
    _store_feature(db, event.id, "currency", info.get("currency"))
    _store_feature(db, event.id, "quote_type", info.get("quoteType"))
    _store_feature(db, event.id, "market", info.get("market"))
    _store_feature(db, event.id, "beta", numeric=info.get("beta"))
    _store_feature(db, event.id, "trailing_pe", numeric=info.get("trailingPE"))
    _store_feature(db, event.id, "forward_pe", numeric=info.get("forwardPE"))
    _store_feature(db, event.id, "enterprise_value", numeric=info.get("enterpriseValue"))
    _store_feature(db, event.id, "revenue", numeric=info.get("totalRevenue"))
    _store_feature(db, event.id, "ebitda", numeric=info.get("ebitda"))
    _store_feature(db, event.id, "total_debt", numeric=info.get("totalDebt"))
    _store_feature(db, event.id, "total_cash", numeric=info.get("totalCash"))
    _store_feature(db, event.id, "full_time_employees", numeric=info.get("fullTimeEmployees"))
    _store_feature(db, event.id, "recommendation_key", info.get("recommendationKey"))

    db.commit()
    return errors


def enrich_events(db: Session, event_ids: Optional[list[int]] = None) -> tuple[int, list[str]]:
    """
    Enrich multiple events. If event_ids is None, enrich all events
    that haven't been enriched yet (no company_name set).
    """
    query = db.query(DislocationEvent)
    if event_ids:
        query = query.filter(DislocationEvent.id.in_(event_ids))
    else:
        # Enrich events missing basic info
        query = query.filter(DislocationEvent.company_name.is_(None))

    events = query.all()
    all_errors: list[str] = []
    count = 0

    for event in events:
        errors = enrich_event(db, event)
        all_errors.extend(errors)
        if not errors:
            count += 1

    return count, all_errors


def _classify_security_type(info: dict, symbol: str) -> str:
    """Classify the security type based on yfinance info."""
    quote_type = (info.get("quoteType") or "").upper()
    name = (info.get("longName") or info.get("shortName") or "").upper()

    if quote_type == "ETF":
        return "etf"

    # SPAC detection
    spac_keywords = ["ACQUISITION", "BLANK CHECK", "SPAC", "MERGER CORP", "CAPITAL CORP"]
    if any(kw in name for kw in spac_keywords):
        return "spac"

    # ADR detection
    if info.get("country") and info.get("country") != "United States":
        return "adr"

    # Closed-end fund detection
    cef_keywords = ["FUND", "TRUST", "INCOME"]
    industry = (info.get("industry") or "").upper()
    if "CLOSED-END" in industry or (
        any(kw in name for kw in cef_keywords) and "ASSET MANAGEMENT" in industry
    ):
        return "closed_end_fund"

    return "common"


def _store_feature(
    db: Session,
    event_id: int,
    name: str,
    value: Optional[str] = None,
    numeric: Optional[float] = None,
) -> None:
    """Store or update a feature for an event."""
    if value is None and numeric is None:
        return

    existing = (
        db.query(DislocationFeature)
        .filter_by(event_id=event_id, feature_name=name)
        .first()
    )

    if existing:
        existing.feature_value = str(value) if value is not None else existing.feature_value
        existing.feature_numeric = float(numeric) if numeric is not None else existing.feature_numeric
    else:
        feat = DislocationFeature(
            event_id=event_id,
            feature_name=name,
            feature_value=str(value) if value is not None else None,
            feature_numeric=float(numeric) if numeric is not None else None,
        )
        db.add(feat)
