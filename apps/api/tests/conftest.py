# apps/api/tests/conftest.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

# Set test env BEFORE importing app/config
TEST_DB_PATH = Path(__file__).parent / "quantpilot_test.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["FRONTEND_URL"] = "http://localhost:8000"
os.environ["COOKIE_SECURE"] = "false"
os.environ["COOKIE_SAMESITE"] = "lax"

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "supersecurepassword"},
    )
    assert resp.status_code == 201, resp.text
    return client


def make_csv_rows(n: int = 80) -> bytes:
    # Deterministic synthetic OHLCV data with trend + oscillation
    lines = ["timestamp,open,high,low,close,volume"]
    price = 100.0
    for i in range(n):
        # A little variation to generate signals
        drift = 0.35 if i % 7 != 0 else -0.8
        price = max(1.0, price + drift)
        o = price - 0.2
        h = price + 0.5
        l = price - 0.6
        c = price
        v = 1000 + i * 10
        ts = f"2024-01-{(i % 28) + 1:02d}T00:00:00"
        # spread across months after 28 rows
        month = 1 + (i // 28)
        ts = f"2024-{month:02d}-{(i % 28) + 1:02d}T00:00:00"
        lines.append(f"{ts},{o:.2f},{h:.2f},{l:.2f},{c:.2f},{v}")
    return ("\n".join(lines)).encode("utf-8")