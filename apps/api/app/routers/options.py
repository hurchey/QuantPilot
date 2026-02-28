"""
Options quant data layer API (Phase A).
Option chain snapshots, risk-free rates, dividends.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from ..deps import get_current_workspace, get_db
from ..models import Workspace
from ..services import options_service as opt_svc
from ..services import rates_service as rates_svc
from ..services import dividends_service as div_svc

router = APIRouter(prefix="/options", tags=["options"])


# --- Phase B: IV + Greeks (must be before /{symbol} routes) ---


@router.post("/greeks")
def compute_option_greeks(
    body: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Compute IV + full Greeks for a single option (Phase B).
    Body: { S, K, T, r?, sigma?, market_price?, option_type? }
    S=spot, K=strike, T=time to expiry (years), r=rate (default from DB).
    Provide sigma OR market_price. option_type: "call" | "put".
    """
    S = body.get("S") or body.get("spot")
    K = body.get("K") or body.get("strike")
    T = body.get("T") or body.get("timeToExpiry")
    if S is None or K is None or T is None:
        raise HTTPException(status_code=400, detail="S, K, T required")
    try:
        S, K, T = float(S), float(K), float(T)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="S, K, T must be numbers")
    r = body.get("r")
    if r is None:
        r = rates_svc.get_risk_free_rate(db)
    else:
        r = float(r)
    sigma = body.get("sigma")
    if sigma is not None:
        sigma = float(sigma)
    market_price = body.get("market_price") or body.get("marketPrice")
    if market_price is not None:
        market_price = float(market_price)
    option_type = body.get("option_type") or body.get("optionType") or "call"
    return opt_svc.compute_greeks_for_option(
        S=S, K=K, T=T, r=r,
        sigma=sigma,
        market_price=market_price,
        option_type=str(option_type),
    )


# --- Live option chain (no auth, like stocks) ---


@router.get("/{symbol}/chain")
def get_option_chain(
    symbol: str,
    expiry: str | None = Query(None, description="Expiry date YYYY-MM-DD"),
    include_greeks: bool = Query(False, description="Compute IV + Greeks for each option (Phase B)"),
    rate: float = Query(0.05, ge=0, le=0.5, description="Risk-free rate (decimal) when include_greeks=True"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Fetch option chain live from yfinance. Not persisted.
    Use POST /options/{symbol}/snapshot to save to your workspace.
    Set include_greeks=true for IV + full Greeks (delta, gamma, theta, vega, rho) per strike.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    try:
        if include_greeks:
            r = rates_svc.get_risk_free_rate(db) if db else rate
            return opt_svc.fetch_option_chain_with_greeks(symbol, expiry, risk_free_rate=r)
        return opt_svc.fetch_option_chain(symbol, expiry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Persisted snapshots (auth required) ---


@router.post("/{symbol}/snapshot")
def create_option_snapshot(
    symbol: str,
    expiry: str | None = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> dict:
    """
    Fetch option chain from yfinance and persist to your workspace.
    Returns summary of stored rows.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    try:
        return opt_svc.persist_option_chain_snapshot(
            db=db,
            workspace_id=workspace.id,
            symbol=symbol,
            expiry=expiry,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/snapshots")
def list_option_snapshots(
    symbol: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List stored option chain snapshots for your workspace."""
    return opt_svc.list_snapshots(
        db=db,
        workspace_id=workspace.id,
        symbol=symbol,
        limit=limit,
    )


@router.get("/{symbol}/snapshots")
def list_symbol_snapshots(
    symbol: str,
    limit: int = Query(50, ge=1, le=200),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List stored option chain snapshots for a symbol."""
    return opt_svc.list_snapshots(
        db=db,
        workspace_id=workspace.id,
        symbol=symbol.strip().upper(),
        limit=limit,
    )


# --- Risk-free rates ---


@router.get("/rates")
def get_rates(
    as_of: str | None = Query(None, description="Date YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get risk-free rate. Uses DB if available, else config default (0.05).
    """
    dt = None
    if as_of:
        try:
            dt = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="as_of must be YYYY-MM-DD")
    rate = rates_svc.get_risk_free_rate(db, as_of=dt)
    return {"rate": rate, "as_of": (dt or datetime.now().date()).isoformat()}


@router.get("/rates/history")
def get_rates_history(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List stored risk-free rates."""
    start = None
    end = None
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date must be YYYY-MM-DD")
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date must be YYYY-MM-DD")
    return rates_svc.list_rates(db, start_date=start, end_date=end, limit=limit)


@router.post("/rates")
def set_rate(
    date: str = Query(..., description="Date YYYY-MM-DD"),
    rate: float = Query(..., ge=0, le=0.5, description="Rate as decimal, e.g. 0.05 for 5%"),
    source: str = Query("manual"),
    db: Session = Depends(get_db),
) -> dict:
    """Store a risk-free rate for a date. No auth for MVP."""
    try:
        dt = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    row = rates_svc.set_risk_free_rate(db, rate_date=dt, rate=rate, source=source)
    return {"date": row.rate_date.strftime("%Y-%m-%d"), "rate": row.rate, "source": row.source}


# --- Dividends ---


@router.get("/dividends/{symbol}")
def get_dividends(
    symbol: str,
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get dividend history for a symbol.
    Uses DB if available, else fetches live from yfinance.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    return div_svc.get_dividends(db, symbol)


@router.post("/dividends/{symbol}/sync")
def sync_dividends(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    """Fetch dividends from yfinance and persist to DB."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    dividends = div_svc.fetch_dividends(symbol)
    stored = div_svc.persist_dividends(db, symbol, dividends)
    return {"symbol": symbol, "stored": stored, "count": len(dividends)}
