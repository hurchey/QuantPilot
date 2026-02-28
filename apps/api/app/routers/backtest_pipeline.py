"""
Backtesting pipeline: universe, data, volatility, trade analysis.

Endpoints for quant backtesting workflow:
- Stock universe (Alpha Vantage LISTING_STATUS)
- Batch data fetch (multi-timeframe)
- Volatility indicator
- Trade analysis (win/loss learning)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_current_workspace, get_db
from ..quant import Bar, load_market_bars
from ..quant.trade_analysis import analyze_all_trades, summarize_learning
from ..quant.volatility import (
    compute_volatility_profile,
    label_volatility_vs_universe,
    profile_to_dict,
)
from ..services import alphavantage as av
from ..services.stock_universe_service import (
    fetch_and_store_batch,
    fetch_and_store_symbol,
    get_active_symbols,
)

router = APIRouter(prefix="/backtest-pipeline", tags=["backtest-pipeline"])


@router.get("/universe")
def get_stock_universe(
    date: str | None = Query(None, description="YYYY-MM-DD for historical universe"),
    state: str = Query("active", description="active or delisted"),
) -> dict[str, Any]:
    """
    Fetch stock universe from Alpha Vantage LISTING_STATUS.
    Survivorship-bias-free: use date for historical snapshot.
    """
    try:
        rows = av.get_listing_status(date=date, state=state)
        symbols = [r["symbol"] for r in rows if r.get("symbol")]
        return {
            "count": len(symbols),
            "symbols": symbols[:500],  # limit response size
            "date": date,
            "state": state,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/fetch-symbol")
def pipeline_fetch_symbol(
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """
    Fetch OHLCV for one symbol from Alpha Vantage and store.
    Supports: 1d, 1d_full, 1w, 1M, 5min, 15min, etc.
    """
    symbol = str(body.get("symbol", "")).strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    timeframe = str(body.get("timeframe", "1d")).strip()
    outputsize = str(body.get("outputsize", "compact")).strip()
    try:
        return fetch_and_store_symbol(
            db,
            workspace_id=workspace.id,
            symbol=symbol,
            timeframe=timeframe,
            outputsize=outputsize,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/fetch-batch")
def pipeline_fetch_batch(
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """
    Batch fetch symbols from Alpha Vantage. Respects rate limits (12.5s between calls).
    """
    symbols = body.get("symbols", [])
    if not symbols:
        raise HTTPException(status_code=400, detail="symbols list required")
    timeframe = str(body.get("timeframe", "1d")).strip()
    outputsize = str(body.get("outputsize", "compact")).strip()
    max_symbols = int(body.get("max_symbols", 20))
    try:
        return fetch_and_store_batch(
            db,
            workspace_id=workspace.id,
            symbols=symbols,
            timeframe=timeframe,
            outputsize=outputsize,
            max_symbols=max_symbols,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/volatility/universe")
def get_universe_volatility(
    symbols: str = Query(..., description="Comma-separated symbols"),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """
    Volatility profiles for multiple symbols, labeled vs cross-sectional average.
    """
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()][:50]
    profiles = []
    for sym in sym_list:
        bars = load_market_bars(
            db=db,
            workspace_id=workspace.id,
            symbol=sym,
            timeframe="1d",
        )
        if len(bars) >= 20:
            profiles.append(compute_volatility_profile(sym, bars))
    label_volatility_vs_universe(profiles)
    return {
        "profiles": [profile_to_dict(p) for p in profiles],
        "count": len(profiles),
    }


@router.get("/volatility/{symbol}")
def get_volatility_profile(
    symbol: str,
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """
    Compute volatility profile for symbol. Requires bars in DB.
    """
    symbol = symbol.strip().upper()
    bars = load_market_bars(
        db=db,
        workspace_id=workspace.id,
        symbol=symbol,
        timeframe="1d",
    )
    if len(bars) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 20 bars for volatility. Got {len(bars)}.",
        )
    profile = compute_volatility_profile(symbol, bars)
    return profile_to_dict(profile)


@router.get("/regime/{symbol}")
def get_regime(
    symbol: str,
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """Detect market regime (trending, mean-reverting, high/low vol)."""
    from ..quant import load_market_bars
    from ..quant.regime import detect_regime

    bars = load_market_bars(db=db, workspace_id=workspace.id, symbol=symbol.strip().upper(), timeframe="1d")
    if len(bars) < 30:
        raise HTTPException(status_code=400, detail="Need at least 30 bars for regime detection")
    state = detect_regime(bars)
    return {
        "symbol": symbol,
        "regime": state.regime,
        "confidence": round(state.confidence, 4),
        "params": state.params,
    }


@router.get("/position-sizing")
def get_position_sizing(
    method: str = Query("vol_target", description="kelly | vol_target | fixed"),
    win_prob: float = Query(0.5),
    win_loss_ratio: float = Query(1.0),
    target_vol: float = Query(0.15),
    asset_vol: float = Query(0.2),
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """Compute position size by method."""
    from dataclasses import asdict

    from ..quant.position_sizing import position_size

    result = position_size(
        method=method,
        win_prob=win_prob,
        win_loss_ratio=win_loss_ratio,
        target_vol=target_vol,
        asset_vol=asset_vol,
    )
    return asdict(result)


@router.get("/sentiment/{symbol}")
def get_sentiment(
    symbol: str,
    limit_per_source: int = Query(30, ge=1, le=100),
    use_ensemble: bool = Query(True, description="Use VADER+FinBERT consensus"),
) -> dict[str, Any]:
    """
    Multi-source sentiment: Alpha Vantage, Finnhub, Stocktwits, Reddit.
    Ensemble NLP (VADER + FinBERT) with consensus. Score 0-100.
    """
    from ..services.sentiment_service import get_sentiment_score

    try:
        s = get_sentiment_score(
            symbol=symbol.strip().upper(),
            limit_per_source=limit_per_source,
            use_ensemble=use_ensemble,
        )
        return {
            "symbol": s.symbol,
            "composite_score": s.composite_score,
            "news_count": s.news_count,
            "social_count": s.social_count,
            "ensemble_sentiment": s.ensemble_sentiment,
            "ensemble_confidence": s.ensemble_confidence,
            "sources": s.sources,
            "raw": s.raw_data,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{run_id}/trade-analysis")
def get_trade_analysis(
    run_id: int,
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    """
    Analyze wins and losses from a backtest run. Learn why trades won or lost.
    """
    from ..models import BacktestRun, Strategy, Trade

    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == run_id, BacktestRun.workspace_id == workspace.id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    strat = db.query(Strategy).filter(Strategy.id == run.strategy_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")

    trades = (
        db.query(Trade)
        .filter(Trade.backtest_run_id == run_id)
        .order_by(Trade.timestamp.asc())
        .all()
    )
    from ..quant.serializers import trade_event_from_db_row

    trade_events = [trade_event_from_db_row(t) for t in trades]
    bars = load_market_bars(
        db=db,
        workspace_id=workspace.id,
        symbol=strat.symbol,
        timeframe=strat.timeframe,
        start_dt=run.start_date,
        end_dt=run.end_date,
    )
    contexts = analyze_all_trades(trade_events, bars)
    summary = summarize_learning(contexts)
    return {
        "run_id": run_id,
        "num_trades_analyzed": len(contexts),
        "summary": summary,
        "trade_contexts": [
            {
                "entry_ts": str(c.entry_ts),
                "exit_ts": str(c.exit_ts),
                "pnl": c.realized_pnl,
                "win": c.win,
                "attribution": c.attribution,
                "holding_bars": c.holding_bars,
                "price_return_pct": round(c.price_return_pct, 2),
            }
            for c in contexts[:50]
        ],
    }
