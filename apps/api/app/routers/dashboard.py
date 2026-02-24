# apps/api/app/routers/dashboard.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_current_workspace, get_db
from ..models import Workspace
from ..services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=schemas.DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
):
    return dashboard_service.get_dashboard_summary(db, workspace_id=workspace.id)


@router.get("/risk", response_model=schemas.DashboardRiskResponse)
def dashboard_risk(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
):
    return dashboard_service.get_dashboard_risk(db, workspace_id=workspace.id)


@router.get("/performance", response_model=schemas.DashboardPerformanceResponse)
def dashboard_performance(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
):
    return dashboard_service.get_dashboard_performance(db, workspace_id=workspace.id)