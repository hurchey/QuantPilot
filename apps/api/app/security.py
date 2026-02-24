# apps/api/app/security.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Use pbkdf2_sha256 to avoid bcrypt's 72-byte password limit
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(*, subject: str, expires_minutes: int | None = None) -> str:
    exp_minutes = expires_minutes or settings.access_token_exp_minutes
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=exp_minutes)

    payload: dict[str, Any] = {
        "sub": subject,  # user id string
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("Invalid or expired token") from e