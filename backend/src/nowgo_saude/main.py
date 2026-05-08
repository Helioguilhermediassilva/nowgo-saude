"""FastAPI app factory for the citizen telemetry ingestion admin API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import events, metrics, pipeline_runs, sources
from .config import get_settings
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="NowGo Saude — Citizen Telemetry Ingestion API",
        version="0.1.0",
        description=(
            "Admin endpoints for the citizen telemetry ingestion pipeline (Feature 001)."
        ),
        lifespan=lifespan,
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    app.include_router(sources.router)
    app.include_router(pipeline_runs.router)
    app.include_router(events.router)
    app.include_router(metrics.router)
    return app


app = create_app()
