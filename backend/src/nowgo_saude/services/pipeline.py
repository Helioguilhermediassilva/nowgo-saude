"""Ingestion pipeline orchestration: anonymize, classify-adjust, persist, audit.

The pipeline is intentionally synchronous in the MVP. Each stage maps directly
onto the FRs in spec.md so contract tests and audit traces line up with the
spec verbatim.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models.pipeline_run import PipelineRun
from ..models.source import Source
from ..models.telemetry_event import TelemetryEvent
from ..schemas import EventIngestRequest
from . import audit as audit_service
from . import pii_vault as pii_vault_service
from .anonymization import AnonymizationResult, anonymize, contains_residual_pii


class IngestionError(Exception):
    """Raised when an ingest payload references an unknown or disabled source."""


def _persist_findings(session: Session, result: AnonymizationResult) -> None:
    """Mirror PII findings into the encrypted vault for later re-identification."""
    for finding in result.findings:
        pii_vault_service.store(
            session,
            token=finding.token,
            category=finding.category,
            value=finding.value,
        )


def _apply_low_confidence_rule(
    severity: int, confidence: float, attributes: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    """FR-003: confidence below threshold downgrades severity and flags the event."""
    threshold = get_settings().classifier_low_confidence_threshold
    if confidence < threshold:
        attributes = {**attributes, "low_confidence": True}
        severity = max(0, severity - 1)
    return severity, attributes


def ingest_event(
    session: Session,
    payload: EventIngestRequest,
    *,
    actor_id: str = "system",
    pipeline_run: PipelineRun | None = None,
) -> TelemetryEvent:
    source = (
        session.query(Source)
        .filter(Source.slug == payload.source_slug, Source.enabled.is_(True))
        .one_or_none()
    )
    if source is None:
        raise IngestionError(f"unknown or disabled source: {payload.source_slug}")

    result = anonymize(payload.text)
    severity, attributes = _apply_low_confidence_rule(
        payload.severity, payload.confidence, payload.attributes
    )

    status = "classified"
    if result.failed or contains_residual_pii(result.text_anonymized):
        status = "quarantined"
    else:
        _persist_findings(session, result)

    event = TelemetryEvent(
        source_id=source.id,
        external_id=payload.external_id,
        received_at=datetime.now(UTC),
        occurred_at=payload.occurred_at,
        region_code=payload.region_code,
        unit_code=payload.unit_code,
        topic=payload.topic,
        subtopic=payload.subtopic,
        sentiment=payload.sentiment,
        severity=severity,
        confidence=payload.confidence,
        text_anonymized=result.text_anonymized,
        pii_tokens=result.pii_tokens,
        attributes=attributes,
        iso_37120=payload.iso_37120,
        iso_37122=payload.iso_37122,
        status=status,
    )
    session.add(event)
    session.flush()

    if pipeline_run is not None:
        pipeline_run.events_collected += 1
        if status == "quarantined":
            pipeline_run.events_quarantined += 1

    audit_service.record(
        session,
        actor_id=actor_id,
        action="event.classify",
        target_kind="event",
        target_id=event.id,
        payload={"source_slug": payload.source_slug, "topic": payload.topic, "status": status},
        metadata={"severity": severity, "confidence": payload.confidence},
    )
    return event


def reprocess_events(
    session: Session,
    event_ids: list[str],
    *,
    actor_id: str = "operator",
    reason: str | None = None,
) -> tuple[PipelineRun, int]:
    events = session.query(TelemetryEvent).filter(TelemetryEvent.id.in_(event_ids)).all()
    if not events:
        raise IngestionError("no matching events to reprocess")

    source_id = events[0].source_id
    run = PipelineRun(source_id=source_id, status="running", metrics={"reason": reason or ""})
    session.add(run)
    session.flush()

    enqueued = 0
    for event in events:
        result = anonymize(event.text_anonymized)
        if result.failed or contains_residual_pii(result.text_anonymized):
            event.status = "quarantined"
        else:
            event.status = "reprocessing"
            event.text_anonymized = result.text_anonymized
            event.pii_tokens = result.pii_tokens
            _persist_findings(session, result)
        enqueued += 1
        audit_service.record(
            session,
            actor_id=actor_id,
            action="event.reprocess",
            target_kind="event",
            target_id=event.id,
            payload={"reason": reason},
            metadata={"pipeline_run_id": run.id},
        )

    run.events_collected = enqueued
    run.status = "succeeded"
    run.finished_at = datetime.now(UTC)
    session.flush()
    return run, enqueued
