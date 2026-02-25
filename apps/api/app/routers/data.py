from __future__ import annotations

import csv
import io
import random
from datetime import datetime, timedelta, timezone
from typing import Any

import pyarrow.parquet as pq
import yfinance as yf
from sqlalchemy import func

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..deps import get_current_workspace, get_db
from ..models import MarketBar

router = APIRouter(prefix="/data", tags=["data"])
datasets_router = APIRouter(prefix="/datasets", tags=["data"])


REQUIRED_CSV_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}


def _generate_demo_bars(symbol: str, timeframe: str, num_days: int = 252) -> list[dict[str, Any]]:
    """Generate synthetic OHLCV bars for demo onboarding (~1 year daily)."""
    base_price = 450.0
    bars = []
    dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    dt = dt - timedelta(days=num_days)
    price = base_price
    for _ in range(num_days):
        change = (random.random() - 0.48) * 2.0
        new_price = max(price * (1 + change / 100), 1.0)
        o, c = price, new_price
        h = max(o, c) * (1 + random.random() * 0.01)
        l = min(o, c) * (1 - random.random() * 0.01)
        vol = int(50_000_000 + random.random() * 30_000_000)
        bars.append({
            "timestamp": dt.replace(tzinfo=None),
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
            "volume": float(vol),
        })
        price = new_price
        dt += timedelta(days=1)
    return bars


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


@router.post("/load-demo")
def load_demo_dataset(
    body: dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """Load built-in demo OHLCV data for easy onboarding. No file upload required."""
    symbol = str(body.get("symbol", "SPY")).strip().upper()
    timeframe = str(body.get("timeframe", "1d")).strip()
    num_days = int(body.get("num_days", 252))
    num_days = max(10, min(1000, num_days))
    bars = _generate_demo_bars(symbol, timeframe, num_days)
    existing_ts = {
        r[0]
        for r in db.query(MarketBar.timestamp)
        .filter(
            MarketBar.workspace_id == workspace.id,
            MarketBar.symbol == symbol,
            MarketBar.timeframe == timeframe,
        )
        .all()
    }
    inserted = 0
    for b in bars:
        if b["timestamp"] in existing_ts:
            continue
        db.add(
            MarketBar(
                workspace_id=workspace.id,
                symbol=symbol,
                timeframe=timeframe,
                timestamp=b["timestamp"],
                open=b["open"],
                high=b["high"],
                low=b["low"],
                close=b["close"],
                volume=b["volume"],
            )
        )
        inserted += 1
    db.commit()
    return {
        "message": "Demo data loaded",
        "symbol": symbol,
        "timeframe": timeframe,
        "rows_inserted": inserted,
        "total_generated": len(bars),
    }


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


PARQUET_COLUMN_ALIASES = {
    "timestamp": ["timestamp", "ts", "datetime", "date", "time", "dt"],
    "open": ["open", "o"],
    "high": ["high", "h"],
    "low": ["low", "l"],
    "close": ["close", "c"],
    "volume": ["volume", "v", "vol"],
}


def _resolve_parquet_columns(columns: list[str]) -> dict[str, str]:
    """Map parquet columns to required OHLCV names."""
    lower_cols = {c.lower(): c for c in columns}
    result = {}
    for required, aliases in PARQUET_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                result[required] = lower_cols[alias]
                break
    return result


@router.post("/upload-parquet")
async def upload_parquet_market_data(
    file: UploadFile = File(...),
    symbol: str = Form(...),
    timeframe: str = Form("1d"),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """Upload Parquet OHLCV file. Common quant/data-engineering format."""
    symbol = symbol.strip().upper()
    timeframe = timeframe.strip()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    if not file.filename or not file.filename.lower().endswith((".parquet", ".pq")):
        raise HTTPException(status_code=400, detail="Please upload a .parquet or .pq file")

    raw = await file.read()
    try:
        table = pq.read_table(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid parquet file: {e}") from e

    columns = table.column_names
    col_map = _resolve_parquet_columns(columns)
    missing = {"timestamp", "open", "high", "low", "close", "volume"} - set(col_map)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Parquet missing required columns: {sorted(missing)}. Found: {columns}",
        )

    existing_ts = {
        r[0]
        for r in db.query(MarketBar.timestamp)
        .filter(
            MarketBar.workspace_id == workspace.id,
            MarketBar.symbol == symbol,
            MarketBar.timeframe == timeframe,
        )
        .all()
    }

    ts_col = table.column(col_map["timestamp"])
    o_col = table.column(col_map["open"])
    h_col = table.column(col_map["high"])
    l_col = table.column(col_map["low"])
    c_col = table.column(col_map["close"])
    v_col = table.column(col_map["volume"])

    inserted = 0
    for i in range(table.num_rows):
        ts_val = ts_col[i]
        if ts_val is None:
            continue
        if hasattr(ts_val, "as_py"):
            ts_val = ts_val.as_py()
        try:
            if isinstance(ts_val, datetime):
                ts = ts_val.replace(tzinfo=None) if ts_val.tzinfo else ts_val
            elif isinstance(ts_val, str):
                ts = _parse_timestamp(ts_val)
            else:
                ts = datetime.fromtimestamp(
                    float(ts_val) / 1e9 if abs(float(ts_val)) > 1e12 else float(ts_val),
                    tz=timezone.utc,
                ).replace(tzinfo=None)
        except Exception:
            continue
        if ts in existing_ts:
            continue
        existing_ts.add(ts)
        o = float(o_col[i]) if o_col[i] is not None else 0.0
        h = float(h_col[i]) if h_col[i] is not None else o
        l = float(l_col[i]) if l_col[i] is not None else o
        c = float(c_col[i]) if c_col[i] is not None else o
        v = float(v_col[i]) if v_col[i] is not None else 0.0
        db.add(
            MarketBar(
                workspace_id=workspace.id,
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
            )
        )
        inserted += 1
    db.commit()
    return {
        "message": "Parquet upload complete",
        "symbol": symbol,
        "timeframe": timeframe,
        "rows_inserted": inserted,
        "uploaded_at": _utcnow_naive().isoformat(),
    }


@router.post("/fetch-symbol")
def fetch_symbol_data(
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """Fetch symbol from market data API (yfinance). Real product workflow."""
    symbol = str(body.get("symbol", "")).strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    timeframe = str(body.get("timeframe", "1d")).strip()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(body.get("days", 365)))
    if "start_date" in body:
        start = _parse_timestamp(str(body["start_date"]))
    if "end_date" in body:
        end = _parse_timestamp(str(body["end_date"]))

    try:
        df = yf.download(
            symbol,
            start=start.date(),
            end=end.date(),
            interval=timeframe,
            progress=False,
            auto_adjust=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fetch failed: {e}") from e

    if df is None or df.empty:
        return {
            "message": "No data returned for symbol",
            "symbol": symbol,
            "timeframe": timeframe,
            "rows_inserted": 0,
        }

    df = df.reset_index()
    col_map: dict[str, Any] = {}
    for c in df.columns:
        c_str = c[0] if isinstance(c, tuple) else str(c)
        c_lower = c_str.lower()
        if c_lower in ("date", "datetime", "timestamp"):
            col_map["timestamp"] = c
        elif c_lower == "open":
            col_map["open"] = c
        elif c_lower == "high":
            col_map["high"] = c
        elif c_lower == "low":
            col_map["low"] = c
        elif c_lower == "close":
            col_map["close"] = c
        elif c_lower == "volume":
            col_map["volume"] = c
    missing = {"timestamp", "open", "high", "low", "close", "volume"} - set(col_map)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"API response missing columns: {sorted(missing)}. Got: {list(df.columns)}",
        )

    existing_ts = {
        r[0]
        for r in db.query(MarketBar.timestamp)
        .filter(
            MarketBar.workspace_id == workspace.id,
            MarketBar.symbol == symbol,
            MarketBar.timeframe == timeframe,
        )
        .all()
    }

    inserted = 0
    for _, row in df.iterrows():
        ts_val = row[col_map["timestamp"]]
        if ts_val is None or (hasattr(ts_val, "year") and (ts_val.year < 1970 or ts_val.year > 2100)):
            continue
        if hasattr(ts_val, "to_pydatetime"):
            ts = ts_val.to_pydatetime()
        elif isinstance(ts_val, datetime):
            ts = ts_val
        else:
            ts = _parse_timestamp(str(ts_val))
        if ts.tzinfo:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            ts = ts.replace(tzinfo=None)
        if ts in existing_ts:
            continue
        existing_ts.add(ts)
        o = float(row[col_map["open"]])
        h = float(row[col_map["high"]])
        l = float(row[col_map["low"]])
        c = float(row[col_map["close"]])
        v = float(row.get(col_map.get("volume"), 0) or 0) if "volume" in col_map else 0.0
        db.add(
            MarketBar(
                workspace_id=workspace.id,
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
            )
        )
        inserted += 1
    db.commit()
    return {
        "message": "Symbol data fetched",
        "symbol": symbol,
        "timeframe": timeframe,
        "rows_inserted": inserted,
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