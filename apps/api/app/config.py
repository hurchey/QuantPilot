# apps/api/app/config.py
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional
    pass


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "QuantPilot API")
    environment: str = os.getenv("ENVIRONMENT", "development")

    # DB
    database_url: str = os.getenv("DATABASE_URL", "").strip()

    # Auth / JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "").strip()
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_exp_minutes: int = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "10080"))  # 7 days

    # Frontend / CORS
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000").strip()

    # Alpha Vantage (stock data API)
    alphavantage_api_key: str = os.getenv("ALPHAVANTAGE_API_KEY", "").strip()

    # Cookie settings
    auth_cookie_name: str = os.getenv("AUTH_COOKIE_NAME", "access_token")
    cookie_secure: bool = _get_bool("COOKIE_SECURE", False)  # False for localhost
    cookie_domain: str | None = os.getenv("COOKIE_DOMAIN", None)
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax")  # "lax" is best for local dev

    def validate(self) -> None:
        missing: list[str] = []
        if not self.database_url:
            missing.append("DATABASE_URL")
        if not self.jwt_secret:
            missing.append("JWT_SECRET")

        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variable(s): {joined}")


settings = Settings()
settings.validate()