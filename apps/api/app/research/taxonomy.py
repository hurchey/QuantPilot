# apps/api/app/research/taxonomy.py
"""
Taxonomy classifier: assigns dislocation events to structural buckets
based on their features and characteristics.

Buckets:
  - short_squeeze: High short interest + rapid covering
  - biotech_catalyst: Biotech/pharma with FDA or trial news
  - spac_despac: SPAC merger completion / de-SPAC pop
  - penny_stock_pump: Sub-$5 stock with low float, high volume spike
  - technical_breakout: Low float + options gamma squeeze characteristics
  - merger_acquisition: M&A announcement or tender offer
  - regulatory_approval: Non-biotech regulatory catalyst (fintech, cannabis, etc.)
  - earnings_surprise: Extreme earnings beat
  - sector_momentum: Sector-wide move (meme stock contagion, etc.)
  - restructuring: Bankruptcy exit, reverse split + rally, debt restructuring
  - unknown: Insufficient data to classify
"""
from __future__ import annotations

from typing import Optional

import logging

from sqlalchemy.orm import Session

from ..models import DislocationEvent, DislocationFeature

logger = logging.getLogger(__name__)

TAXONOMY_BUCKETS = [
    "short_squeeze",
    "biotech_catalyst",
    "spac_despac",
    "penny_stock_pump",
    "technical_breakout",
    "merger_acquisition",
    "regulatory_approval",
    "earnings_surprise",
    "sector_momentum",
    "restructuring",
    "unknown",
]


def classify_event(event: DislocationEvent) -> tuple[str, float, str]:
    """
    Classify a single event into a taxonomy bucket.

    Returns (bucket, confidence, notes).
    Confidence is 0.0-1.0 indicating how sure the classification is.
    """
    scores: dict[str, float] = {b: 0.0 for b in TAXONOMY_BUCKETS}
    notes: list[str] = []

    sector = (event.sector or "").lower()
    industry = (event.industry or "").lower()
    sec_type = (event.security_type or "").lower()
    name = (event.company_name or "").lower()

    # --- Short squeeze signals ---
    if event.short_pct_float and event.short_pct_float > 0.15:
        scores["short_squeeze"] += 0.4
        notes.append(f"Short % of float: {event.short_pct_float:.1%}")
    if event.days_to_cover and event.days_to_cover > 5:
        scores["short_squeeze"] += 0.2
        notes.append(f"Days to cover: {event.days_to_cover:.1f}")
    if event.volume_ratio and event.volume_ratio > 20:
        scores["short_squeeze"] += 0.15
        notes.append(f"Volume ratio: {event.volume_ratio:.0f}x")

    # --- Biotech catalyst ---
    biotech_sectors = ["healthcare", "biotechnology"]
    biotech_industries = [
        "biotechnology", "pharmaceuticals", "drug manufacturers",
        "diagnostics", "medical devices",
    ]
    if sector in biotech_sectors or any(bi in industry for bi in biotech_industries):
        scores["biotech_catalyst"] += 0.5
        notes.append(f"Sector: {event.sector}, Industry: {event.industry}")

    # --- SPAC / de-SPAC ---
    if sec_type == "spac":
        scores["spac_despac"] += 0.7
        notes.append("Security type: SPAC")
    spac_name_signals = ["acquisition", "merger", "spac", "blank check"]
    if any(s in name for s in spac_name_signals):
        scores["spac_despac"] += 0.3
        notes.append(f"SPAC name signals in: {event.company_name}")

    # --- Penny stock pump ---
    if event.price_start and event.price_start < 5.0:
        scores["penny_stock_pump"] += 0.25
        notes.append(f"Pre-event price: ${event.price_start:.2f}")
    if event.float_shares and event.float_shares < 20_000_000:
        scores["penny_stock_pump"] += 0.2
        notes.append(f"Low float: {event.float_shares:,.0f}")
    if event.market_cap_pre and event.market_cap_pre < 100_000_000:
        scores["penny_stock_pump"] += 0.15
        notes.append(f"Micro-cap: ${event.market_cap_pre:,.0f}")

    # --- Technical breakout / gamma squeeze ---
    if event.options_available == 1 and event.volume_ratio and event.volume_ratio > 10:
        scores["technical_breakout"] += 0.25
    if event.float_shares and event.float_shares < 10_000_000 and event.options_available == 1:
        scores["technical_breakout"] += 0.2
        notes.append("Low float + options available (gamma squeeze candidate)")

    # --- Restructuring ---
    restructure_signals = ["restructur", "bankruptcy", "chapter 11", "reverse split"]
    if any(s in name for s in restructure_signals):
        scores["restructuring"] += 0.5
        notes.append("Restructuring signals in name")

    # --- Recent IPO / listing ---
    if event.days_since_ipo is not None and event.days_since_ipo < 90:
        notes.append(f"Recent listing: {event.days_since_ipo} days since IPO")
        # Boosts SPAC or penny stock scores
        scores["spac_despac"] += 0.1
        scores["penny_stock_pump"] += 0.1

    # --- Pick the winner ---
    best_bucket = max(scores, key=lambda k: scores[k])
    best_score = scores[best_bucket]

    if best_score < 0.15:
        best_bucket = "unknown"
        best_score = 0.0
        notes.append("Insufficient signals for confident classification")

    # Normalize confidence to 0-1
    confidence = min(best_score, 1.0)

    return best_bucket, round(confidence, 2), "; ".join(notes)


def classify_events(db: Session, event_ids: Optional[list[int]] = None) -> tuple[int, dict[str, int]]:
    """
    Classify multiple events. Returns (count_classified, bucket_counts).
    """
    query = db.query(DislocationEvent)
    if event_ids:
        query = query.filter(DislocationEvent.id.in_(event_ids))
    else:
        # Classify events that haven't been classified yet
        query = query.filter(DislocationEvent.taxonomy_bucket.is_(None))

    events = query.all()
    bucket_counts: dict[str, int] = {}
    count = 0

    for event in events:
        bucket, confidence, notes = classify_event(event)
        event.taxonomy_bucket = bucket
        event.taxonomy_confidence = confidence
        event.taxonomy_notes = notes
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        count += 1

    db.commit()
    return count, bucket_counts
