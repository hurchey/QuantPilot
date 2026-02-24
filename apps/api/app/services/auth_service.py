# apps/api/app/services/auth_service.py
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User, Workspace
from ..security import create_access_token, hash_password, verify_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
        max_age=settings.access_token_exp_minutes * 60,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        domain=settings.cookie_domain,
        path="/",
    )


def register_user(db: Session, *, email: str, password: str) -> User:
    email = normalize_email(email)

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(password) > 512:
        raise HTTPException(status_code=400, detail="Password is too long")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()

    workspace = Workspace(user_id=user.id, name="Default Workspace")
    db.add(workspace)

    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    email = normalize_email(email)

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return user


def issue_login_cookie(response: Response, *, user: User) -> str:
    token = create_access_token(subject=str(user.id))
    set_auth_cookie(response, token)
    return token


def get_me_payload(db: Session, *, user: User) -> dict[str, Any]:
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