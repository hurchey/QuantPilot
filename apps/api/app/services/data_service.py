# apps/api/app/services/data_service.py
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..models import MarketBar


REQUIRED_CSV_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_timestamp(value: str) -> datetime:
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


def market_bar_to_dict(row: MarketBar) -> dict[str, Any]:
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


async def upload_csv_market_data(
    db: Session,
    *,
    workspace_id: int,
    file: UploadFile,
    symbol: str,
    timeframe: str = "1d",
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

    existing_rows = (
        db.query(MarketBar.timestamp)
        .filter(
            MarketBar.workspace_id == workspace_id,
            MarketBar.symbol == symbol,
            MarketBar.timeframe == timeframe,
        )
        .all()
    )
    existing_ts = {r[0] for r in existing_rows}

    seen_in_file: set[datetime] = set()
    to_insert: list[MarketBar] = []
    skipped_duplicates = 0

    for idx, row in enumerate(reader, start=2):
        try:
            ts = parse_timestamp(str(row.get("timestamp", "")))
            if ts in existing_ts or ts in seen_in_file:
                skipped_duplicates += 1
                continue

            seen_in_file.add(ts)

            to_insert.append(
                MarketBar(
                    workspace_id=workspace_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=ts,
                    open=float(row.get("open", 0)),
                    high=float(row.get("high", 0)),
                    low=float(row.get("low", 0)),
                    close=float(row.get("close", 0)),
                    volume=float(row.get("volume", 0) or 0),
                )
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CSV parse error on line {idx}: {e}") from e

    if to_insert:
        db.add_all(to_insert)
        db.commit()

    return {
        "message": "Upload complete",
        "symbol": symbol,
        "timeframe": timeframe,
        "rows_inserted": len(to_insert),
        "rows_skipped_duplicates": skipped_duplicates,
        "uploaded_at": utcnow_naive().isoformat(),
    }


def list_symbols(db: Session, *, workspace_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(MarketBar.symbol, MarketBar.timeframe)
        .filter(MarketBar.workspace_id == workspace_id)
        .distinct()
        .order_by(MarketBar.symbol.asc(), MarketBar.timeframe.asc())
        .all()
    )
    return [{"symbol": r[0], "timeframe": r[1]} for r in rows]


def get_bars(
    db: Session,
    *,
    workspace_id: int,
    symbol: str,
    timeframe: str = "1d",
    start: str | None = None,
    end: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    q = (
        db.query(MarketBar)
        .filter(
            MarketBar.workspace_id == workspace_id,
            MarketBar.symbol == symbol.strip().upper(),
            MarketBar.timeframe == timeframe.strip(),
        )
        .order_by(MarketBar.timestamp.asc())
    )

    if start:
        q = q.filter(MarketBar.timestamp >= parse_timestamp(start))
    if end:
        q = q.filter(MarketBar.timestamp <= parse_timestamp(end))

    rows = q.limit(limit).all()
    return [market_bar_to_dict(r) for r in rows]