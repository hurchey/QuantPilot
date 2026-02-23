from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Response
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

COOKIE_NAME = "access_token"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# First scheme is used for NEW hashes (argon2)
# bcrypt remains for verifying older hashes if you already created any.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=True,  # explicit if bcrypt edge cases happen
)


def hash_password(password: str) -> str:
    # Force new hashes to use argon2
    return pwd_context.hash(password, scheme="argon2")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        # Handles bcrypt 72-byte errors and malformed hashes gracefully
        return False


def password_needs_rehash(hashed_password: str) -> bool:
    # Useful for migrating old bcrypt hashes to argon2 after login
    try:
        return pwd_context.needs_update(hashed_password)
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        sub = payload.get("sub")
        if sub is None:
            raise ValueError("Invalid token payload")
        return int(sub)
    except (JWTError, ValueError, TypeError):
        raise ValueError("Invalid token")


def set_auth_cookie(response: Response, token: str) -> None:
    # For local dev on http://localhost, secure must be False
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")