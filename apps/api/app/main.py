# apps/api/app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routers import auth, backtests, dashboard, data, health, strategies


def _build_allowed_origins(frontend_url: str) -> list[str]:
    origins = {frontend_url.rstrip("/")}

    # Add localhost/127.0.0.1 mirror automatically for local dev convenience
    if "localhost" in frontend_url:
        origins.add(frontend_url.replace("localhost", "127.0.0.1").rstrip("/"))
    if "127.0.0.1" in frontend_url:
        origins.add(frontend_url.replace("127.0.0.1", "localhost").rstrip("/"))

    # Common local ports if you switch around
    origins.update(
        {
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
        }
    )

    return sorted(origins)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    # For MVP only. Later, use Alembic migrations.
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_allowed_origins(settings.frontend_url),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(strategies.router)
app.include_router(data.router)
app.include_router(backtests.router)
app.include_router(dashboard.router)