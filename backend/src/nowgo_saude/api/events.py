"""Event ingestion and reprocessing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..schemas import (
    EventIngestRequest,
    ReprocessRequest,
    ReprocessResponse,
    TelemetryEventOut,
)
from ..services.pipeline import IngestionError, ingest_event, reprocess_events
from .deps import db_session, require_admin

router = APIRouter(prefix="/api/v1", tags=["events"])


def _to_event_out(event) -> dict:  # type: ignore[no-untyped-def]
    return {
        "id": event.id,
        "source_slug": event.source.slug,
        "external_id": event.external_id,
        "received_at": event.received_at,
        "occurred_at": event.occurred_at,
        "region_code": event.region_code,
        "unit_code": event.unit_code,
        "topic": event.topic,
        "subtopic": event.subtopic,
        "sentiment": event.sentiment,
        "severity": event.severity,
        "confidence": float(event.confidence),
        "text_anonymized": event.text_anonymized,
        "pii_tokens": event.pii_tokens,
        "attributes": event.attributes,
        "iso_37120": event.iso_37120,
        "iso_37122": event.iso_37122,
        "status": event.status,
    }


@router.post("/events", response_model=TelemetryEventOut, status_code=status.HTTP_201_CREATED)
def ingest(
    payload: EventIngestRequest,
    session: Session = Depends(db_session),
    actor: str = Depends(require_admin),
) -> dict:
    try:
        event = ingest_event(session, payload, actor_id=actor)
    except IngestionError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_source", "message": str(exc)},
        ) from exc
    session.commit()
    session.refresh(event)
    return _to_event_out(event)


@router.post(
    "/events:reprocess",
    response_model=ReprocessResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def reprocess(
    payload: ReprocessRequest,
    session: Session = Depends(db_session),
    actor: str = Depends(require_admin),
) -> ReprocessResponse:
    try:
        run, enqueued = reprocess_events(
            session, payload.event_ids, actor_id=actor, reason=payload.reason
        )
    except IngestionError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "no_events", "message": str(exc)},
        ) from exc
    session.commit()
    return ReprocessResponse(pipeline_run_id=run.id, enqueued=enqueued)
