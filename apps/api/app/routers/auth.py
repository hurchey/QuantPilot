# apps/api/app/routers/auth.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_current_user, get_db
from ..models import User, Workspace
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # "lax" for local dev
        domain=settings.cookie_domain,
        path="/",
        max_age=settings.access_token_exp_minutes * 60,
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        domain=settings.cookie_domain,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: dict[str, Any] = Body(...),
    response: Response = None,  # FastAPI injects
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    email = _normalize_email(str(payload.get("email", "")))
    password = str(payload.get("password", ""))

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(password) > 512:
        raise HTTPException(status_code=400, detail="Password is too long")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(password),
        created_at=_utcnow_naive(),
        updated_at=_utcnow_naive(),
    )
    db.add(user)
    db.flush()

    # Create default workspace immediately
    workspace = Workspace(
        user_id=user.id,
        name="Default Workspace",
        created_at=_utcnow_naive(),
        updated_at=_utcnow_naive(),
    )
    db.add(workspace)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    _set_auth_cookie(response, token)

    return {
        "message": "Registered successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


@router.post("/login")
def login(
    payload: dict[str, Any] = Body(...),
    response: Response = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    email = _normalize_email(str(payload.get("email", "")))
    password = str(payload.get("password", ""))

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=str(user.id))
    _set_auth_cookie(response, token)

    return {
        "message": "Logged in successfully",
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    _clear_auth_cookie(response)
    return {"message": "Logged out"}


@router.get("/me")
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    workspace = db.query(Workspace).filter(Workspace.user_id == user.id).first()
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
        } if workspace else None,
    }