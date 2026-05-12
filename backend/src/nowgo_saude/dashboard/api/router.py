"""Command Center Dashboard API (Feature 002).

Read-only, admin-bearer-protected aggregations consumed by the Next.js
dashboard. All responses use camelCase JSON to match the frontend types.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...api.deps import db_session, require_admin
from ..schemas import (
    AlertEventList,
    AttentionUnitList,
    KPIList,
    PipelineHealthOut,
    RegionDetailOut,
    RegionPressureList,
    TimeSeriesList,
    TopicSliceList,
    UnitDetailOut,
)
from ..services.aggregations import (
    heatmap_by_ra,
    region_detail,
    time_series,
    topic_breakdown,
    unit_detail,
)
from ..services.alerts import derive_alerts
from ..services.health import pipeline_health
from ..services.kpis import compute_kpis
from ..services.units import attention_units

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get(
    "/health",
    response_model=PipelineHealthOut,
    response_model_by_alias=True,
)
def health(
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> PipelineHealthOut:
    return pipeline_health(session)


@router.get(
    "/kpis",
    response_model=KPIList,
    response_model_by_alias=True,
)
def kpis(
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> KPIList:
    return KPIList(items=compute_kpis(session))


@router.get(
    "/heatmap",
    response_model=RegionPressureList,
    response_model_by_alias=True,
)
def heatmap(
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> RegionPressureList:
    return RegionPressureList(items=heatmap_by_ra(session))


@router.get(
    "/regions/{ra_id}",
    response_model=RegionDetailOut,
    response_model_by_alias=True,
)
def region(
    ra_id: str,
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> RegionDetailOut:
    detail = region_detail(session, ra_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Região {ra_id} not found")
    return detail


@router.get(
    "/units/attention",
    response_model=AttentionUnitList,
    response_model_by_alias=True,
)
def attention(
    limit: int = Query(default=12, ge=1, le=50),
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> AttentionUnitList:
    return AttentionUnitList(items=attention_units(session, limit=limit))


@router.get(
    "/units/{unit_id}",
    response_model=UnitDetailOut,
    response_model_by_alias=True,
)
def unit(
    unit_id: str,
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> UnitDetailOut:
    detail = unit_detail(session, unit_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Unidade {unit_id} not found")
    return detail


@router.get(
    "/topics",
    response_model=TopicSliceList,
    response_model_by_alias=True,
)
def topics(
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> TopicSliceList:
    return TopicSliceList(items=topic_breakdown(session))


@router.get(
    "/timeseries",
    response_model=TimeSeriesList,
    response_model_by_alias=True,
)
def timeseries(
    hours: int = Query(default=24, ge=1, le=168),
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> TimeSeriesList:
    return TimeSeriesList(items=time_series(session, hours))


@router.get(
    "/alerts",
    response_model=AlertEventList,
    response_model_by_alias=True,
)
def alerts(
    limit: int = Query(default=12, ge=1, le=50),
    session: Session = Depends(db_session),
    _: str = Depends(require_admin),
) -> AlertEventList:
    return AlertEventList(items=derive_alerts(session, limit=limit))
