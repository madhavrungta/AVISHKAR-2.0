"""FastAPI application entry point for SIH 26162 Phase 1."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.database import dispose_database, initialize_database
from app.logging_config import configure_logging


LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize PostGIS when available without preventing diagnostic startup."""

    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.database_ready = False
    try:
        initialize_database()
        app.state.database_ready = True
        LOGGER.info("PostGIS is ready")
    except Exception:
        LOGGER.warning("PostGIS is unavailable; database-backed endpoints will return 503", exc_info=True)
    yield
    dispose_database()


app = FastAPI(
    title="SIH 26162 Thermal Anomaly API",
    version="0.1.0",
    description=(
        "Phase 1 ingestion and inspection of NASA FIRMS thermal anomalies. "
        "Records are not confirmed fires or industrial classifications."
    ),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


@app.get("/health")
def health(request: Request) -> dict[str, str]:
    """Return API and database readiness for operators and Compose health checks."""

    return {
        "status": "ok",
        "database": "ready" if getattr(request.app.state, "database_ready", False) else "unavailable",
    }

