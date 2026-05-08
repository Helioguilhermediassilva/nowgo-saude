"""Sources admin endpoints (CRUD subset)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.source import Source
from ..schemas import SourceCreate, SourceOut, SourceUpdate
from .deps import db_session, require_admin

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(
    enabled: bool | None = Query(default=None),
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> list[Source]:
    query = session.query(Source)
    if enabled is not None:
        query = query.filter(Source.enabled.is_(enabled))
    return query.order_by(Source.slug).all()


@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreate,
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> Source:
    source = Source(
        slug=payload.slug,
        kind=payload.kind,
        display_name=payload.display_name,
        enabled=payload.enabled,
        config=payload.config,
        retention_policy=payload.retention_policy.model_dump(),
        iso_37120_default=payload.iso_37120_default,
    )
    session.add(source)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "source_conflict", "message": "slug already exists"},
        ) from None
    session.refresh(source)
    return source


def _get_or_404(session: Session, slug: str) -> Source:
    source = session.query(Source).filter(Source.slug == slug).one_or_none()
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "source_not_found", "message": f"unknown slug {slug!r}"},
        )
    return source


@router.get("/{slug}", response_model=SourceOut)
def get_source(
    slug: str,
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> Source:
    return _get_or_404(session, slug)


@router.patch("/{slug}", response_model=SourceOut)
def update_source(
    slug: str,
    payload: SourceUpdate,
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> Source:
    source = _get_or_404(session, slug)
    data = payload.model_dump(exclude_unset=True)
    if "retention_policy" in data and data["retention_policy"] is not None:
        data["retention_policy"] = (
            data["retention_policy"]
            if isinstance(data["retention_policy"], dict)
            else data["retention_policy"].model_dump()
        )
    for field, value in data.items():
        setattr(source, field, value)
    session.commit()
    session.refresh(source)
    return source
