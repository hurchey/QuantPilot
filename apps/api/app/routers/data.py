from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..deps import get_current_workspace, get_db
from ..models import MarketBar

router = APIRouter(prefix="/data", tags=["data"])
datasets_router = APIRouter(prefix="/datasets", tags=["data"])


REQUIRED_CSV_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_timestamp(value: str) -> datetime:
    v = value.strip()
    if not v:
        raise ValueError("Empty timestamp")

    # ISO support (including Z)
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        pass

    # Common fallback formats
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue

    raise ValueError(f"Invalid timestamp format: {value}")


def _list_datasets_impl(db: Session, workspace: Any) -> list[dict[str, Any]]:
    rows = (
        db.query(
            MarketBar.symbol,
            MarketBar.timeframe,
            func.count(MarketBar.id).label("row_count"),
            func.min(MarketBar.timestamp).label("created_at"),
        )
        .filter(MarketBar.workspace_id == workspace.id)
        .group_by(MarketBar.symbol, MarketBar.timeframe)
        .order_by(MarketBar.symbol.asc(), MarketBar.timeframe.asc())
        .all()
    )
    return [
        {
            "id": idx,
            "name": f"{r.symbol} {r.timeframe}",
            "symbol": r.symbol,
            "timeframe": r.timeframe,
            "row_count": r.row_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for idx, r in enumerate(rows)
    ]


@router.get("")
def list_datasets(
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> list[dict[str, Any]]:
    """List datasets (symbol/timeframe pairs) with row counts. Serves GET /quant/data."""
    return _list_datasets_impl(db, workspace)


@datasets_router.get("")
def list_datasets_alias(
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> list[dict[str, Any]]:
    """List datasets. Serves GET /quant/datasets (frontend fallback)."""
    return _list_datasets_impl(db, workspace)


def _bar_to_dict(row: MarketBar) -> dict[str, Any]:
    return {
        "id": row.id,
        "workspace_id": row.workspace_id,
        "symbol": row.symbol,
        "timeframe": row.timeframe,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "open": float(row.open),
        "high": float(row.high),
        "low": float(row.low),
        "close": float(row.close),
        "volume": float(row.volume or 0),
    }


@router.post("/upload")
async def upload_csv_market_data(
    file: UploadFile = File(...),
    symbol: str = Form(...),
    timeframe: str = Form("1d"),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    symbol = symbol.strip().upper()
    timeframe = timeframe.strip()

    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV is empty or invalid")

    normalized_headers = {h.strip().lower() for h in reader.fieldnames if h}
    missing = REQUIRED_CSV_COLUMNS - normalized_headers
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {sorted(missing)}",
        )

    # De-dup against existing timestamps for this symbol/timeframe/workspace
    existing_rows = (
        db.query(MarketBar.timestamp)
        .filter(
            MarketBar.workspace_id == workspace.id,
            MarketBar.symbol == symbol,
            MarketBar.timeframe == timeframe,
        )
        .all()
    )
    existing_ts = {r[0] for r in existing_rows}

    inserted = 0
    skipped_duplicates = 0
    seen_in_file: set[datetime] = set()

    for idx, row in enumerate(reader, start=2):
        try:
            ts = _parse_timestamp(str(row.get("timestamp", "")))
            if ts in existing_ts or ts in seen_in_file:
                skipped_duplicates += 1
                continue
            seen_in_file.add(ts)

            bar = MarketBar(
                workspace_id=workspace.id,
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts,
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                volume=float(row.get("volume", 0) or 0),
            )
            db.add(bar)
            inserted += 1
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"CSV parse error on line {idx}: {e}",
            ) from e

    db.commit()

    return {
        "message": "Upload complete",
        "symbol": symbol,
        "timeframe": timeframe,
        "rows_inserted": inserted,
        "rows_skipped_duplicates": skipped_duplicates,
        "uploaded_at": _utcnow_naive().isoformat(),
    }


@router.get("/symbols")
def list_symbols(
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> list[dict[str, Any]]:
    # Distinct symbol/timeframe pairs
    rows = (
        db.query(MarketBar.symbol, MarketBar.timeframe)
        .filter(MarketBar.workspace_id == workspace.id)
        .distinct()
        .order_by(MarketBar.symbol.asc(), MarketBar.timeframe.asc())
        .all()
    )
    return [{"symbol": r[0], "timeframe": r[1]} for r in rows]


@router.get("/bars")
def get_bars(
    symbol: str = Query(...),
    timeframe: str = Query("1d"),
    start: str | None = Query(None),
    end: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> list[dict[str, Any]]:
    q = (
        db.query(MarketBar)
        .filter(
            MarketBar.workspace_id == workspace.id,
            MarketBar.symbol == symbol.strip().upper(),
            MarketBar.timeframe == timeframe.strip(),
        )
        .order_by(MarketBar.timestamp.asc())
    )

    if start:
        q = q.filter(MarketBar.timestamp >= _parse_timestamp(start))
    if end:
        q = q.filter(MarketBar.timestamp <= _parse_timestamp(end))

    rows = q.limit(limit).all()
    return [_bar_to_dict(r) for r in rows]