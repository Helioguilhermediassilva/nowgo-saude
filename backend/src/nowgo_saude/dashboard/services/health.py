"""Pipeline health summary for the dashboard header.

Reuses the data feeding ``/api/v1/metrics`` but reshapes it into the contract
the Next.js dashboard expects (``PipelineHealth``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ...config import get_settings
from ...models.telemetry_event import TelemetryEvent
from ..schemas import PipelineHealthOut


def pipeline_health(session: Session) -> PipelineHealthOut:
    threshold = get_settings().health_latency_threshold_seconds
    now = datetime.now(UTC)
    last_ingestion = (
        session.query(func.max(TelemetryEvent.received_at))
        .filter(TelemetryEvent.status == "classified")
        .scalar()
    )
    last_ingestion = last_ingestion or (now - timedelta(hours=1))
    if last_ingestion.tzinfo is None:
        last_ingestion = last_ingestion.replace(tzinfo=UTC)

    age_seconds = (now - last_ingestion).total_seconds()
    if age_seconds > threshold * 4:
        status = "down"
        message = f"Sem ingestão há {int(age_seconds)}s"
    elif age_seconds > threshold:
        status = "degraded"
        message = f"Última ingestão há {int(age_seconds)}s (limite {int(threshold)}s)"
    else:
        status = "ok"
        message = None

    return PipelineHealthOut(
        status=status,  # type: ignore[arg-type]
        latency_p95_seconds=round(min(age_seconds, threshold * 4), 1),
        threshold_seconds=threshold,
        last_successful_ingestion_at=last_ingestion,
        message=message,
    )
