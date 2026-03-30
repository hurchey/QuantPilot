# apps/api/app/research/universe_builder.py
"""
Universe builder orchestrator: combines all data sources to build
the complete dataset of extreme dislocation events.

Pipeline:
  1. Gather tickers from multiple sources (EDGAR, seed list, FTD signals)
  2. Scan all tickers for 500%+ 3-day moves
  3. Persist events to database
  4. Enrich with fundamentals
  5. Classify into taxonomy buckets

Designed to run in stages — each step is idempotent and can be re-run.
"""
from __future__ import annotations

from typing import Optional

import logging
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import DislocationEvent
from .edgar import build_full_ticker_universe, get_high_ftd_symbols
from .enricher import enrich_events
from .scanner import scan_symbol, get_universe_symbols
from .seed_list import SEED_EVENTS, get_seed_symbols
from .taxonomy import classify_events

logger = logging.getLogger(__name__)


@dataclass
class UniverseBuildResult:
    """Result of a universe build run."""
    tickers_scanned: int = 0
    events_found: int = 0
    events_persisted: int = 0
    events_enriched: int = 0
    events_classified: int = 0
    errors: list[str] = field(default_factory=list)
    ticker_sources: dict[str, int] = field(default_factory=dict)


def build_universe_from_seeds(
    db: Session,
    start_date: str = "2019-01-01",
    end_date: Optional[str] = None,
    min_return_3d_pct: float = 100.0,
) -> UniverseBuildResult:
    """
    Phase 1a: Scan the curated seed list of known extreme movers.
    Best for validating the pipeline.
    """
    result = UniverseBuildResult()
    symbols = get_seed_symbols()
    result.ticker_sources["seed_list"] = len(symbols)

    _scan_and_persist(db, symbols, start_date, end_date, min_return_3d_pct, result)

    # Also store the known catalyst from seed data
    _tag_seed_catalysts(db)

    return result


def build_universe_from_edgar(
    db: Session,
    start_date: str = "2019-01-01",
    end_date: Optional[str] = None,
    min_return_3d_pct: float = 100.0,
    batch_size: int = 50,
    max_tickers: Optional[int] = None,
) -> UniverseBuildResult:
    """
    Phase 1b: Scan the full SEC EDGAR universe.
    This is the comprehensive scan — can take hours for thousands of tickers.

    Args:
        batch_size: Process tickers in batches (for progress tracking)
        max_tickers: Limit total tickers scanned (for testing)
    """
    result = UniverseBuildResult()

    # Get all U.S. equity tickers from EDGAR
    universe_df = build_full_ticker_universe()
    tickers = universe_df["ticker"].tolist()

    if max_tickers:
        tickers = tickers[:max_tickers]

    result.ticker_sources["edgar"] = len(tickers)
    logger.info("Starting EDGAR universe scan: %d tickers", len(tickers))

    # Process in batches
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        logger.info("Scanning batch %d-%d of %d", i, i + len(batch), len(tickers))
        _scan_and_persist(db, batch, start_date, end_date, min_return_3d_pct, result)

    return result


def build_universe_from_ftd_signals(
    db: Session,
    years: Optional[list[int]] = None,
    start_date: str = "2019-01-01",
    end_date: Optional[str] = None,
    min_return_3d_pct: float = 100.0,
) -> UniverseBuildResult:
    """
    Phase 1c: Find symbols with high Failures to Deliver, then scan them.
    High FTD symbols are prime squeeze candidates.
    """
    result = UniverseBuildResult()

    if years is None:
        current_year = datetime.now().year
        years = list(range(2020, current_year + 1))

    ftd_symbols: set[str] = set()
    for year in years:
        for half in [1, 2]:
            try:
                high_ftd = get_high_ftd_symbols(year, half)
                if not high_ftd.empty:
                    ftd_symbols.update(high_ftd["symbol"].tolist())
            except Exception as e:
                result.errors.append(f"FTD {year} H{half}: {e}")

    symbols = sorted(ftd_symbols)
    result.ticker_sources["ftd_signals"] = len(symbols)
    logger.info("Found %d high-FTD symbols to scan", len(symbols))

    _scan_and_persist(db, symbols, start_date, end_date, min_return_3d_pct, result)
    return result


def build_universe_combined(
    db: Session,
    start_date: str = "2019-01-01",
    end_date: Optional[str] = None,
    min_return_3d_pct: float = 100.0,
    include_edgar: bool = True,
    include_ftd: bool = True,
    edgar_max_tickers: Optional[int] = None,
    enrich: bool = True,
    classify: bool = True,
) -> UniverseBuildResult:
    """
    Full pipeline: combine all sources, scan, enrich, and classify.

    This is the main entry point for building the complete dataset.
    """
    result = UniverseBuildResult()

    # 1. Seed list (always included — fast, known events)
    logger.info("=== Stage 1: Seed list scan ===")
    seed_symbols = get_seed_symbols()
    result.ticker_sources["seed_list"] = len(seed_symbols)
    _scan_and_persist(db, seed_symbols, start_date, end_date, min_return_3d_pct, result)
    _tag_seed_catalysts(db)

    # 2. EDGAR full universe
    if include_edgar:
        logger.info("=== Stage 2: EDGAR universe scan ===")
        try:
            universe_df = build_full_ticker_universe()
            edgar_tickers = universe_df["ticker"].tolist()

            # Remove tickers we already scanned
            already_scanned = set(seed_symbols)
            edgar_tickers = [t for t in edgar_tickers if t not in already_scanned]

            if edgar_max_tickers:
                edgar_tickers = edgar_tickers[:edgar_max_tickers]

            result.ticker_sources["edgar"] = len(edgar_tickers)
            _scan_and_persist(db, edgar_tickers, start_date, end_date, min_return_3d_pct, result)
        except Exception as e:
            result.errors.append(f"EDGAR scan failed: {e}")

    # 3. FTD signals
    if include_ftd:
        logger.info("=== Stage 3: FTD signal scan ===")
        try:
            ftd_result = build_universe_from_ftd_signals(
                db, start_date=start_date, end_date=end_date,
                min_return_3d_pct=min_return_3d_pct,
            )
            result.errors.extend(ftd_result.errors)
            result.ticker_sources["ftd_signals"] = ftd_result.ticker_sources.get("ftd_signals", 0)
        except Exception as e:
            result.errors.append(f"FTD scan failed: {e}")

    # 4. Enrich all un-enriched events
    if enrich:
        logger.info("=== Stage 4: Enriching events ===")
        try:
            count, errors = enrich_events(db)
            result.events_enriched = count
            result.errors.extend(errors)
        except Exception as e:
            result.errors.append(f"Enrichment failed: {e}")

    # 5. Classify all unclassified events
    if classify:
        logger.info("=== Stage 5: Classifying events ===")
        try:
            count, _ = classify_events(db)
            result.events_classified = count
        except Exception as e:
            result.errors.append(f"Classification failed: {e}")

    # Final count
    result.events_found = db.query(DislocationEvent).count()
    logger.info(
        "Universe build complete: %d events found, %d enriched, %d classified",
        result.events_found, result.events_enriched, result.events_classified,
    )

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _scan_and_persist(
    db: Session,
    symbols: list[str],
    start_date: str,
    end_date: Optional[str],
    min_return_3d_pct: float,
    result: UniverseBuildResult,
) -> None:
    """Scan symbols and persist results to database."""
    for symbol in symbols:
        result.tickers_scanned += 1
        try:
            events = scan_symbol(symbol, start_date, end_date, min_return_3d_pct)
            for event_data in events:
                existing = (
                    db.query(DislocationEvent)
                    .filter_by(
                        symbol=event_data["symbol"],
                        event_start_date=event_data["event_start_date"],
                    )
                    .first()
                )
                if not existing:
                    obj = DislocationEvent(**event_data)
                    db.add(obj)
                    result.events_persisted += 1

            if events:
                db.commit()
        except Exception as e:
            result.errors.append(f"{symbol}: {e}")
            db.rollback()


def _tag_seed_catalysts(db: Session) -> None:
    """
    Tag events from the seed list with their known catalyst as a
    starting taxonomy_bucket (can be overridden by the classifier later).
    """
    for seed in SEED_EVENTS:
        events = (
            db.query(DislocationEvent)
            .filter(
                DislocationEvent.symbol == seed["symbol"],
                DislocationEvent.taxonomy_bucket.is_(None),
            )
            .all()
        )
        for event in events:
            event.catalyst_summary = seed.get("notes", "")
            # Only set taxonomy if not already classified
            if not event.taxonomy_bucket:
                event.taxonomy_bucket = seed.get("catalyst")
                event.taxonomy_confidence = 0.9  # high confidence for known events
                event.taxonomy_notes = f"Seed list: {seed.get('notes', '')}"

    db.commit()
