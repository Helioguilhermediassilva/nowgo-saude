"""Pipeline runs listing endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..models.pipeline_run import PipelineRun
from ..models.source import Source
from ..schemas import PipelineRunOut
from .deps import db_session, require_admin

router = APIRouter(prefix="/api/v1/pipeline-runs", tags=["pipeline-runs"])


@router.get("", response_model=list[PipelineRunOut])
def list_pipeline_runs(
    source_slug: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern=r"^(running|succeeded|partial|failed)$"),
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> list[PipelineRun]:
    query = session.query(PipelineRun)
    if source_slug:
        query = query.join(Source, PipelineRun.source_id == Source.id).filter(
            Source.slug == source_slug
        )
    if status:
        query = query.filter(PipelineRun.status == status)
    return query.order_by(PipelineRun.started_at.desc()).limit(limit).all()
