import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # loads apps/api/.env when run from apps/api


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


@dataclass
class Settings:
    database_url: str
    frontend_url: str
    jwt_secret: str
    jwt_alg: str


settings = Settings(
    database_url=_require("DATABASE_URL"),
    frontend_url=os.getenv("FRONTEND_URL", "http://localhost:8000"),
    jwt_secret=_require("JWT_SECRET"),
    jwt_alg=os.getenv("JWT_ALG", "HS256"),
)