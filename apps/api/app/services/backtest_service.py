# apps/api/app/services/backtest_service.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import BacktestRun, EquityPoint, Strategy, Trade
from ..quant import (
    BacktestConfig,
    build_db_rows_for_result,
    load_market_bars,
    run_sma_crossover_backtest,
)


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_dt(value: Any, field_name: str) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {value}") from e

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def run_to_dict(run: BacktestRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "workspace_id": run.workspace_id,
        "strategy_id": run.strategy_id,
        "start_date": run.start_date.isoformat() if run.start_date else None,
        "end_date": run.end_date.isoformat() if run.end_date else None,
        "initial_capital": float(run.initial_capital),
        "fees_bps": float(run.fees_bps),
        "slippage_bps": float(run.slippage_bps),
        "status": run.status,
        "metrics_json": run.metrics_json or {},
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def trade_to_dict(t: Trade) -> dict[str, Any]:
    return {
        "id": t.id,
        "backtest_run_id": t.backtest_run_id,
        "symbol": t.symbol,
        "side": t.side,
        "qty": float(t.qty),
        "price": float(t.price),
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
        "fee": float(t.fee or 0),
        "realized_pnl": None if t.realized_pnl is None else float(t.realized_pnl),
    }


def equity_to_dict(e: EquityPoint) -> dict[str, Any]:
    return {
        "id": e.id,
        "backtest_run_id": e.backtest_run_id,
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        "equity": float(e.equity),
        "drawdown": float(e.drawdown or 0),
    }


def get_backtest_run(db: Session, *, workspace_id: int, run_id: int) -> BacktestRun:
    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == run_id, BacktestRun.workspace_id == workspace_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return run


def run_backtest(db: Session, *, workspace_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    strategy_id = payload.get("strategy_id")
    if not strategy_id:
        raise HTTPException(status_code=400, detail="strategy_id is required")

    strategy = (
        db.query(Strategy)
        .filter(Strategy.id == int(strategy_id), Strategy.workspace_id == workspace_id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if strategy.strategy_type != "sma_crossover":
        raise HTTPException(status_code=400, detail="Only sma_crossover is supported right now")

    params = strategy.parameters_json or {}
    fast_window = int(params.get("fast_window", 10))
    slow_window = int(params.get("slow_window", 30))

    start_dt = parse_dt(payload.get("start_date"), "start_date")
    end_dt = parse_dt(payload.get("end_date"), "end_date")
    initial_capital = float(payload.get("initial_capital", 10_000))
    fees_bps = float(payload.get("fees_bps", 1))
    slippage_bps = float(payload.get("slippage_bps", 1))

    bars = load_market_bars(
        db=db,
        workspace_id=workspace_id,
        symbol=strategy.symbol,
        timeframe=strategy.timeframe,
        start_dt=start_dt,
        end_dt=end_dt,
    )
    if len(bars) < slow_window + 2:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough bars to run strategy. Need > {slow_window + 1}, got {len(bars)}",
        )

    run = BacktestRun(
        workspace_id=workspace_id,
        strategy_id=strategy.id,
        start_date=start_dt or bars[0].timestamp,
        end_date=end_dt or bars[-1].timestamp,
        initial_capital=initial_capital,
        fees_bps=fees_bps,
        slippage_bps=slippage_bps,
        status="running",
        metrics_json={},
        completed_at=None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        result = run_sma_crossover_backtest(
            bars=bars,
            config=BacktestConfig(
                symbol=strategy.symbol,
                timeframe=strategy.timeframe,
                initial_capital=initial_capital,
                fees_bps=fees_bps,
                slippage_bps=slippage_bps,
            ),
            fast_window=fast_window,
            slow_window=slow_window,
        )

        rows = build_db_rows_for_result(backtest_run_id=run.id, result=result)

        run.metrics_json = rows["metrics_json"]
        run.status = "completed"
        run.completed_at = utcnow_naive()

        trade_objects = [Trade(**row) for row in rows["trade_rows"]]
        equity_objects = [EquityPoint(**row) for row in rows["equity_rows"]]

        if trade_objects:
            db.add_all(trade_objects)
        if equity_objects:
            db.add_all(equity_objects)

        db.commit()
        db.refresh(run)

        return {
            "message": "Backtest completed",
            "run": run_to_dict(run),
            "meta": {
                "strategy_type": strategy.strategy_type,
                "symbol": strategy.symbol,
                "timeframe": strategy.timeframe,
                "fast_window": fast_window,
                "slow_window": slow_window,
                "bars_used": len(bars),
            },
        }

    except HTTPException:
        db.rollback()
        failed = db.query(BacktestRun).filter(BacktestRun.id == run.id).first()
        if failed:
            failed.status = "failed"
            failed.completed_at = utcnow_naive()
            db.commit()
        raise
    except Exception as e:
        db.rollback()
        failed = db.query(BacktestRun).filter(BacktestRun.id == run.id).first()
        if failed:
            failed.status = "failed"
            failed.completed_at = utcnow_naive()
            failed.metrics_json = {"error": str(e)}
            db.commit()
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}") from e


def list_backtests(
    db: Session,
    *,
    workspace_id: int,
    strategy_id: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    q = db.query(BacktestRun).filter(BacktestRun.workspace_id == workspace_id)
    if strategy_id is not None:
        q = q.filter(BacktestRun.strategy_id == strategy_id)

    rows = q.order_by(BacktestRun.created_at.desc()).limit(limit).all()
    return [run_to_dict(r) for r in rows]


def get_backtest_detail(db: Session, *, workspace_id: int, run_id: int) -> dict[str, Any]:
    run = get_backtest_run(db, workspace_id=workspace_id, run_id=run_id)
    strategy = db.query(Strategy).filter(Strategy.id == run.strategy_id).first()

    return {
        "run": run_to_dict(run),
        "strategy": {
            "id": strategy.id,
            "name": strategy.name,
            "symbol": strategy.symbol,
            "timeframe": strategy.timeframe,
            "strategy_type": strategy.strategy_type,
            "parameters_json": strategy.parameters_json or {},
        } if strategy else None,
    }


def get_backtest_trades(db: Session, *, workspace_id: int, run_id: int) -> list[dict[str, Any]]:
    _ = get_backtest_run(db, workspace_id=workspace_id, run_id=run_id)

    rows = (
        db.query(Trade)
        .filter(Trade.backtest_run_id == run_id)
        .order_by(Trade.timestamp.asc())
        .all()
    )
    return [trade_to_dict(t) for t in rows]


def get_backtest_equity(db: Session, *, workspace_id: int, run_id: int) -> list[dict[str, Any]]:
    _ = get_backtest_run(db, workspace_id=workspace_id, run_id=run_id)

    rows = (
        db.query(EquityPoint)
        .filter(EquityPoint.backtest_run_id == run_id)
        .order_by(EquityPoint.timestamp.asc())
        .all()
    )
    return [equity_to_dict(e) for e in rows]


def get_backtest_metrics(db: Session, *, workspace_id: int, run_id: int) -> dict[str, Any]:
    run = get_backtest_run(db, workspace_id=workspace_id, run_id=run_id)
    return run.metrics_json or {}