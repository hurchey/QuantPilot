from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_current_workspace, get_db
from ..models import Strategy

router = APIRouter(prefix="/strategies", tags=["strategies"])


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _strategy_to_dict(s: Strategy) -> dict[str, Any]:
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_strategy(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
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

    now = _utcnow_naive()
    strategy = Strategy(
        workspace_id=workspace.id,
        name=name,
        strategy_type=strategy_type,
        symbol=symbol,
        timeframe=timeframe,
        parameters_json=params,
        created_at=now,
        updated_at=now,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return _strategy_to_dict(strategy)


@router.get("")
def list_strategies(
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> list[dict[str, Any]]:
    rows = (
        db.query(Strategy)
        .filter(Strategy.workspace_id == workspace.id)
        .order_by(Strategy.created_at.desc())
        .all()
    )
    return [_strategy_to_dict(s) for s in rows]


@router.get("/{strategy_id}")
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    strategy = (
        db.query(Strategy)
        .filter(Strategy.id == strategy_id, Strategy.workspace_id == workspace.id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return _strategy_to_dict(strategy)


@router.patch("/{strategy_id}")
def update_strategy(
    strategy_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, Any]:
    strategy = (
        db.query(Strategy)
        .filter(Strategy.id == strategy_id, Strategy.workspace_id == workspace.id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

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

    strategy.updated_at = _utcnow_naive()
    db.commit()
    db.refresh(strategy)
    return _strategy_to_dict(strategy)


@router.delete("/{strategy_id}")
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    workspace=Depends(get_current_workspace),
) -> dict[str, str]:
    strategy = (
        db.query(Strategy)
        .filter(Strategy.id == strategy_id, Strategy.workspace_id == workspace.id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    db.delete(strategy)
    db.commit()
    return {"message": "Strategy deleted"}