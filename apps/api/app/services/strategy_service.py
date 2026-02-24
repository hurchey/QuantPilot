# apps/api/app/services/strategy_service.py
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Strategy


def strategy_to_dict(s: Strategy) -> dict[str, Any]:
    return {
        "id": s.id,
        "workspace_id": s.workspace_id,
        "name": s.name,
        "strategy_type": s.strategy_type,
        "symbol": s.symbol,
        "timeframe": s.timeframe,
        "parameters_json": s.parameters_json or {},
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def create_strategy(db: Session, *, workspace_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    strategy_type = str(payload.get("strategy_type", "")).strip()
    symbol = str(payload.get("symbol", "")).strip().upper()
    timeframe = str(payload.get("timeframe", "1d")).strip()
    params = payload.get("parameters_json", {}) or {}

    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not strategy_type:
        raise HTTPException(status_code=400, detail="strategy_type is required")
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="parameters_json must be an object")

    strategy = Strategy(
        workspace_id=workspace_id,
        name=name,
        strategy_type=strategy_type,
        symbol=symbol,
        timeframe=timeframe,
        parameters_json=params,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)

    return strategy_to_dict(strategy)


def list_strategies(db: Session, *, workspace_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(Strategy)
        .filter(Strategy.workspace_id == workspace_id)
        .order_by(Strategy.created_at.desc())
        .all()
    )
    return [strategy_to_dict(s) for s in rows]


def get_strategy(db: Session, *, workspace_id: int, strategy_id: int) -> Strategy:
    strategy = (
        db.query(Strategy)
        .filter(Strategy.id == strategy_id, Strategy.workspace_id == workspace_id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


def get_strategy_dict(db: Session, *, workspace_id: int, strategy_id: int) -> dict[str, Any]:
    return strategy_to_dict(get_strategy(db, workspace_id=workspace_id, strategy_id=strategy_id))


def update_strategy(
    db: Session,
    *,
    workspace_id: int,
    strategy_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    strategy = get_strategy(db, workspace_id=workspace_id, strategy_id=strategy_id)

    if "name" in payload:
        strategy.name = str(payload["name"]).strip()
    if "strategy_type" in payload:
        strategy.strategy_type = str(payload["strategy_type"]).strip()
    if "symbol" in payload:
        strategy.symbol = str(payload["symbol"]).strip().upper()
    if "timeframe" in payload:
        strategy.timeframe = str(payload["timeframe"]).strip()
    if "parameters_json" in payload:
        if not isinstance(payload["parameters_json"], dict):
            raise HTTPException(status_code=400, detail="parameters_json must be an object")
        strategy.parameters_json = payload["parameters_json"]

    db.commit()
    db.refresh(strategy)
    return strategy_to_dict(strategy)


def delete_strategy(db: Session, *, workspace_id: int, strategy_id: int) -> dict[str, str]:
    strategy = get_strategy(db, workspace_id=workspace_id, strategy_id=strategy_id)
    db.delete(strategy)
    db.commit()
    return {"message": "Strategy deleted"}