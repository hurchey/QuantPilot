# apps/api/app/services/dashboard_service.py
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import BacktestRun, EquityPoint, Strategy


def get_dashboard_summary(db: Session, *, workspace_id: int) -> dict[str, Any]:
    strategies_count = db.query(Strategy).filter(Strategy.workspace_id == workspace_id).count()

    runs = (
        db.query(BacktestRun)
        .filter(BacktestRun.workspace_id == workspace_id)
        .order_by(BacktestRun.created_at.desc())
        .all()
    )

    latest_run = runs[0] if runs else None
    best_sharpe = None
    best_total_return = None

    for r in runs:
        metrics = r.metrics_json or {}
        sharpe = metrics.get("sharpe")
        total_return = metrics.get("total_return")

        if isinstance(sharpe, (int, float)):
            if best_sharpe is None or float(sharpe) > best_sharpe:
                best_sharpe = float(sharpe)

        if isinstance(total_return, (int, float)):
            if best_total_return is None or float(total_return) > best_total_return:
                best_total_return = float(total_return)

    return {
        "strategies_count": strategies_count,
        "backtests_count": len(runs),
        "latest_run_id": latest_run.id if latest_run else None,
        "latest_status": latest_run.status if latest_run else None,
        "latest_metrics": (latest_run.metrics_json or {}) if latest_run else {},
        "best_sharpe": best_sharpe,
        "best_total_return": best_total_return,
    }


def get_dashboard_risk(db: Session, *, workspace_id: int) -> dict[str, Any]:
    latest_run = (
        db.query(BacktestRun)
        .filter(BacktestRun.workspace_id == workspace_id)
        .order_by(BacktestRun.created_at.desc())
        .first()
    )

    if not latest_run:
        return {
            "latest_run_id": None,
            "sharpe": None,
            "volatility": None,
            "max_drawdown": None,
            "win_rate": None,
        }

    metrics = latest_run.metrics_json or {}
    return {
        "latest_run_id": latest_run.id,
        "sharpe": metrics.get("sharpe"),
        "volatility": metrics.get("volatility"),
        "max_drawdown": metrics.get("max_drawdown"),
        "win_rate": metrics.get("win_rate"),
    }


def get_dashboard_performance(db: Session, *, workspace_id: int) -> dict[str, Any]:
    latest_run = (
        db.query(BacktestRun)
        .filter(BacktestRun.workspace_id == workspace_id)
        .order_by(BacktestRun.created_at.desc())
        .first()
    )

    if not latest_run:
        return {"latest_run_id": None, "equity_curve": [], "recent_runs": []}

    equity = (
        db.query(EquityPoint)
        .filter(EquityPoint.backtest_run_id == latest_run.id)
        .order_by(EquityPoint.timestamp.asc())
        .all()
    )

    recent_runs = (
        db.query(BacktestRun)
        .filter(BacktestRun.workspace_id == workspace_id)
        .order_by(BacktestRun.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "latest_run_id": latest_run.id,
        "equity_curve": [
            {
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                "equity": float(p.equity),
                "drawdown": float(p.drawdown or 0),
            }
            for p in equity
        ],
        "recent_runs": [
            {
                "id": r.id,
                "strategy_id": r.strategy_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "status": r.status,
                "total_return": (r.metrics_json or {}).get("total_return"),
                "sharpe": (r.metrics_json or {}).get("sharpe"),
                "max_drawdown": (r.metrics_json or {}).get("max_drawdown"),
            }
            for r in recent_runs
        ],
    }