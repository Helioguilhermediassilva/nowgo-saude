"""Operational metrics endpoint."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.telemetry_event import TelemetryEvent
from ..schemas import MetricsSummary
from .deps import db_session, require_admin

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("", response_model=MetricsSummary)
def metrics_summary(
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> MetricsSummary:
    now = datetime.now(UTC)
    one_minute_ago = now - timedelta(minutes=1)
    twenty_four_hours_ago = now - timedelta(hours=24)

    epm = (
        session.query(func.count(TelemetryEvent.id))
        .filter(TelemetryEvent.received_at >= one_minute_ago)
        .scalar()
        or 0
    )
    dlq = (
        session.query(func.count(TelemetryEvent.id))
        .filter(TelemetryEvent.status == "quarantined")
        .scalar()
        or 0
    )
    failures_24h = (
        session.query(func.count(TelemetryEvent.id))
        .filter(
            TelemetryEvent.status == "quarantined",
            TelemetryEvent.received_at >= twenty_four_hours_ago,
        )
        .scalar()
        or 0
    )
    return MetricsSummary(
        events_per_minute=float(epm),
        p95_latency_ms=0.0,
        dlq_depth=int(dlq),
        anonymization_failures_24h=int(failures_24h),
        updated_at=now,
    )
