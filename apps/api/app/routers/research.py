# apps/api/app/routers/research.py
"""
API router for extreme dislocation research.

Endpoints:
  POST /research/scan              - Scan symbols for 500%+ 3-day moves
  POST /research/scan-universe     - Scan a predefined universe
  POST /research/build-seeds       - Build dataset from curated seed list
  POST /research/build-edgar       - Build dataset from full SEC EDGAR universe
  POST /research/build-ftd         - Build dataset from high-FTD symbols
  POST /research/build-full        - Full pipeline: seeds + EDGAR + FTD + enrich + classify
  GET  /research/seed-list         - View the curated seed list
  GET  /research/ftd-signals       - View high-FTD symbols for a given period
  GET  /research/events            - List all dislocation events
  GET  /research/events/{id}       - Get event detail with features
  POST /research/enrich            - Enrich events with float/fundamentals
  POST /research/classify          - Assign taxonomy buckets
  GET  /research/stats             - Dataset statistics
  GET  /research/export            - Export dataset as JSON or CSV
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import DislocationEvent, DislocationFeature
from ..research.edgar import get_high_ftd_symbols
from ..research.enricher import enrich_events
from ..research.scanner import get_universe_symbols, scan_symbols
from ..research.seed_list import SEED_EVENTS, get_seed_symbols, get_seed_catalysts
from ..research.universe_builder import (
    build_universe_from_seeds,
    build_universe_from_edgar,
    build_universe_from_ftd_signals,
    build_universe_combined,
)
from ..research.schemas import (
    ClassifyRequest,
    ClassifyResponse,
    DatasetExportRequest,
    DatasetStatsOut,
    DislocationEventDetailOut,
    DislocationEventOut,
    DislocationFeatureOut,
    EnrichRequest,
    EnrichResponse,
    ScanRequest,
    ScanResponse,
    ScanResult,
    ScanSymbolListRequest,
)
from ..research.taxonomy import classify_events

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Scan endpoints ---


@router.post("/scan", response_model=ScanResponse)
def scan_for_dislocations(req: ScanRequest, db: Session = Depends(get_db)):
    """Scan a list of symbols for extreme 3-day dislocations."""
    events, errors = scan_symbols(
        symbols=req.symbols,
        start_date=req.start_date,
        end_date=req.end_date,
        min_return_3d_pct=req.min_return_3d_pct,
    )

    # Persist events to database
    persisted = _persist_events(db, events)

    results = [
        ScanResult(
            symbol=e["symbol"],
            event_start_date=e["event_start_date"].strftime("%Y-%m-%d"),
            return_3d_pct=e["return_3d_pct"],
            return_1d_pct=e.get("return_1d_pct"),
            price_start=e["price_start"],
            price_peak=e["price_peak"],
            label_a=e["label_a"] == 1,
            label_b=e["label_b"] == 1,
        )
        for e in events
    ]

    return ScanResponse(
        total_symbols_scanned=len(req.symbols),
        total_events_found=len(events),
        events=results,
        errors=errors,
    )


@router.post("/scan-universe", response_model=ScanResponse)
def scan_universe(req: ScanSymbolListRequest, db: Session = Depends(get_db)):
    """Scan a predefined universe (sp500, russell2000, all_us) for dislocations."""
    if req.universe == "custom":
        if not req.custom_symbols:
            raise HTTPException(400, "custom_symbols required when universe='custom'")
        symbols = req.custom_symbols
    else:
        symbols = get_universe_symbols(req.universe)
        if not symbols:
            raise HTTPException(404, f"Could not load symbols for universe '{req.universe}'")

    events, errors = scan_symbols(
        symbols=symbols,
        start_date=req.start_date,
        end_date=req.end_date,
        min_return_3d_pct=req.min_return_3d_pct,
    )

    _persist_events(db, events)

    results = [
        ScanResult(
            symbol=e["symbol"],
            event_start_date=e["event_start_date"].strftime("%Y-%m-%d"),
            return_3d_pct=e["return_3d_pct"],
            return_1d_pct=e.get("return_1d_pct"),
            price_start=e["price_start"],
            price_peak=e["price_peak"],
            label_a=e["label_a"] == 1,
            label_b=e["label_b"] == 1,
        )
        for e in events
    ]

    return ScanResponse(
        total_symbols_scanned=len(symbols),
        total_events_found=len(events),
        events=results,
        errors=errors,
    )


# --- Universe building endpoints ---


@router.get("/seed-list")
def view_seed_list():
    """View the curated seed list of known extreme movers."""
    return {
        "total": len(SEED_EVENTS),
        "catalysts": get_seed_catalysts(),
        "events": SEED_EVENTS,
    }


@router.post("/build-seeds")
def build_from_seeds(
    start_date: str = "2019-01-01",
    min_return_3d_pct: float = 100.0,
    db: Session = Depends(get_db),
):
    """
    Build dataset from the curated seed list (~35 known extreme movers).
    Fast — good for validating the pipeline.
    """
    result = build_universe_from_seeds(db, start_date=start_date, min_return_3d_pct=min_return_3d_pct)
    return {
        "tickers_scanned": result.tickers_scanned,
        "events_found": result.events_found,
        "events_persisted": result.events_persisted,
        "ticker_sources": result.ticker_sources,
        "errors": result.errors[:50],  # cap error output
    }


@router.post("/build-edgar")
def build_from_edgar(
    start_date: str = "2019-01-01",
    min_return_3d_pct: float = 100.0,
    max_tickers: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Build dataset from the full SEC EDGAR universe.
    WARNING: This scans thousands of tickers and can take hours.
    Use max_tickers to limit for testing (e.g. max_tickers=100).
    """
    result = build_universe_from_edgar(
        db, start_date=start_date, min_return_3d_pct=min_return_3d_pct,
        max_tickers=max_tickers,
    )
    return {
        "tickers_scanned": result.tickers_scanned,
        "events_found": result.events_found,
        "events_persisted": result.events_persisted,
        "ticker_sources": result.ticker_sources,
        "errors": result.errors[:50],
    }


@router.post("/build-ftd")
def build_from_ftd(
    start_date: str = "2019-01-01",
    min_return_3d_pct: float = 100.0,
    db: Session = Depends(get_db),
):
    """
    Build dataset from symbols with high Failures to Deliver (SEC FTD data).
    These are prime squeeze candidates.
    """
    result = build_universe_from_ftd_signals(
        db, start_date=start_date, min_return_3d_pct=min_return_3d_pct,
    )
    return {
        "tickers_scanned": result.tickers_scanned,
        "events_found": result.events_found,
        "events_persisted": result.events_persisted,
        "ticker_sources": result.ticker_sources,
        "errors": result.errors[:50],
    }


@router.post("/build-full")
def build_full_pipeline(
    start_date: str = "2019-01-01",
    min_return_3d_pct: float = 100.0,
    include_edgar: bool = True,
    include_ftd: bool = True,
    edgar_max_tickers: Optional[int] = None,
    enrich: bool = True,
    classify: bool = True,
    db: Session = Depends(get_db),
):
    """
    Full pipeline: seeds + EDGAR + FTD signals + enrich + classify.
    This builds the complete dataset end-to-end.

    Use edgar_max_tickers to limit the EDGAR scan for testing.
    Set include_edgar=false or include_ftd=false to skip those stages.
    """
    result = build_universe_combined(
        db,
        start_date=start_date,
        min_return_3d_pct=min_return_3d_pct,
        include_edgar=include_edgar,
        include_ftd=include_ftd,
        edgar_max_tickers=edgar_max_tickers,
        enrich=enrich,
        classify=classify,
    )
    return {
        "tickers_scanned": result.tickers_scanned,
        "events_found": result.events_found,
        "events_persisted": result.events_persisted,
        "events_enriched": result.events_enriched,
        "events_classified": result.events_classified,
        "ticker_sources": result.ticker_sources,
        "errors": result.errors[:50],
    }


@router.get("/ftd-signals")
def view_ftd_signals(
    year: int = 2024,
    half: int = 1,
    min_ftd_quantity: int = 500_000,
):
    """View symbols with high Failures to Deliver for a given period."""
    df = get_high_ftd_symbols(year, half, min_ftd_quantity=min_ftd_quantity)
    if df.empty:
        return {"total": 0, "symbols": []}
    return {
        "total": len(df),
        "symbols": df.to_dict(orient="records"),
    }


# --- Event CRUD ---


@router.get("/events", response_model=list[DislocationEventOut])
def list_events(
    label: Optional[str] = Query(None, description="'A' for 500%+, 'B' for 1000%+"),
    taxonomy_bucket: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List dislocation events with optional filters."""
    query = db.query(DislocationEvent)

    if label == "A":
        query = query.filter(DislocationEvent.label_a == 1)
    elif label == "B":
        query = query.filter(DislocationEvent.label_b == 1)

    if taxonomy_bucket:
        query = query.filter(DislocationEvent.taxonomy_bucket == taxonomy_bucket)

    events = (
        query.order_by(DislocationEvent.return_3d_pct.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return events


@router.get("/events/{event_id}", response_model=DislocationEventDetailOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a single dislocation event with all its features."""
    event = db.query(DislocationEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    features = db.query(DislocationFeature).filter_by(event_id=event_id).all()

    return DislocationEventDetailOut(
        event=DislocationEventOut.model_validate(event),
        features=[DislocationFeatureOut.model_validate(f) for f in features],
    )


# --- Enrich & classify ---


@router.post("/enrich", response_model=EnrichResponse)
def enrich(req: EnrichRequest, db: Session = Depends(get_db)):
    """Enrich dislocation events with float, fundamentals, and structural data."""
    count, errors = enrich_events(db, event_ids=req.event_ids)
    return EnrichResponse(events_enriched=count, errors=errors)


@router.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest, db: Session = Depends(get_db)):
    """Assign taxonomy buckets to dislocation events."""
    count, bucket_counts = classify_events(db, event_ids=req.event_ids)
    return ClassifyResponse(events_classified=count, bucket_counts=bucket_counts)


# --- Stats & export ---


@router.get("/stats", response_model=DatasetStatsOut)
def dataset_stats(db: Session = Depends(get_db)):
    """Get summary statistics for the dislocation dataset."""
    total = db.query(DislocationEvent).count()
    label_a = db.query(DislocationEvent).filter(DislocationEvent.label_a == 1).count()
    label_b = db.query(DislocationEvent).filter(DislocationEvent.label_b == 1).count()

    # Continuation rate
    cont_events = (
        db.query(DislocationEvent)
        .filter(DislocationEvent.day_after_continuation.isnot(None))
        .all()
    )
    cont_rate = None
    if cont_events:
        cont_rate = sum(1 for e in cont_events if e.day_after_continuation == 1) / len(cont_events)

    # Bucket distribution
    buckets: dict[str, int] = {}
    bucket_rows = (
        db.query(DislocationEvent.taxonomy_bucket)
        .filter(DislocationEvent.taxonomy_bucket.isnot(None))
        .all()
    )
    for (b,) in bucket_rows:
        buckets[b] = buckets.get(b, 0) + 1

    # Top symbols by event count
    from sqlalchemy import func

    top = (
        db.query(DislocationEvent.symbol, func.count(DislocationEvent.id).label("count"))
        .group_by(DislocationEvent.symbol)
        .order_by(func.count(DislocationEvent.id).desc())
        .limit(20)
        .all()
    )
    top_symbols = [{"symbol": s, "count": c} for s, c in top]

    return DatasetStatsOut(
        total_events=total,
        label_a_count=label_a,
        label_b_count=label_b,
        continuation_rate=round(cont_rate, 4) if cont_rate is not None else None,
        bucket_distribution=buckets,
        top_symbols=top_symbols,
    )


@router.get("/export")
def export_dataset(
    format: str = Query("json", description="'json' or 'csv'"),
    label: Optional[str] = Query(None),
    taxonomy_bucket: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export the dislocation dataset as JSON or CSV."""
    query = db.query(DislocationEvent)

    if label == "A":
        query = query.filter(DislocationEvent.label_a == 1)
    elif label == "B":
        query = query.filter(DislocationEvent.label_b == 1)
    if taxonomy_bucket:
        query = query.filter(DislocationEvent.taxonomy_bucket == taxonomy_bucket)

    events = query.order_by(DislocationEvent.return_3d_pct.desc()).all()

    if format == "csv":
        return _export_csv(events)

    # Default: JSON
    rows = [DislocationEventOut.model_validate(e).model_dump(mode="json") for e in events]
    return rows


# --- Helpers ---


def _persist_events(db: Session, events: list[dict]) -> int:
    """Persist scan results to database, skipping duplicates."""
    count = 0
    for event_data in events:
        existing = (
            db.query(DislocationEvent)
            .filter_by(
                symbol=event_data["symbol"],
                event_start_date=event_data["event_start_date"],
            )
            .first()
        )
        if existing:
            continue

        obj = DislocationEvent(**event_data)
        db.add(obj)
        count += 1

    db.commit()
    return count


def _export_csv(events: list[DislocationEvent]) -> StreamingResponse:
    """Generate a CSV streaming response."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "id", "symbol", "company_name", "security_type",
        "event_start_date", "event_end_date",
        "price_start", "price_peak", "price_end_3d",
        "return_1d_pct", "return_3d_pct", "return_peak_pct",
        "label_a", "label_b", "day_after_continuation",
        "volume_event_day", "volume_avg_20d_pre", "volume_ratio",
        "shares_outstanding", "float_shares", "market_cap_pre",
        "short_interest_shares", "short_pct_float", "days_to_cover",
        "sector", "industry", "exchange",
        "ipo_date", "days_since_ipo",
        "options_available",
        "taxonomy_bucket", "taxonomy_confidence", "taxonomy_notes",
    ]
    writer.writerow(headers)

    for e in events:
        writer.writerow([
            e.id, e.symbol, e.company_name, e.security_type,
            e.event_start_date, e.event_end_date,
            e.price_start, e.price_peak, e.price_end_3d,
            e.return_1d_pct, e.return_3d_pct, e.return_peak_pct,
            e.label_a, e.label_b, e.day_after_continuation,
            e.volume_event_day, e.volume_avg_20d_pre, e.volume_ratio,
            e.shares_outstanding, e.float_shares, e.market_cap_pre,
            e.short_interest_shares, e.short_pct_float, e.days_to_cover,
            e.sector, e.industry, e.exchange,
            e.ipo_date, e.days_since_ipo,
            e.options_available,
            e.taxonomy_bucket, e.taxonomy_confidence, e.taxonomy_notes,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dislocations.csv"},
    )
