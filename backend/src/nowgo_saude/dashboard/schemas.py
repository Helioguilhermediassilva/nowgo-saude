"""Pydantic schemas for the Command Center Dashboard API (Feature 002).

Field names use snake_case in Python but emit camelCase JSON via
``serialization_alias`` so the Next.js dashboard can pass-through responses
without remapping.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SmartCityFramework = Literal["ISO 37120", "ITU-T Y.4900", "IMD Smart City"]
Severity = Literal["low", "medium", "high", "critical"]
OperationalTopic = Literal[
    "fila", "infraestrutura", "atendimento", "medicamento", "agendamento", "outros"
]
Trend = Literal["up", "down", "stable"]
HealthStatus = Literal["ok", "degraded", "down"]
AlertStatus = Literal["open", "acknowledged", "resolved"]


class _CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class KPIOut(_CamelModel):
    id: str
    name: str
    value: float
    unit: str
    delta: float | None = None
    framework: SmartCityFramework
    reference: str
    source: str
    updated_at: datetime = Field(serialization_alias="updatedAt")


class RegionPressureOut(_CamelModel):
    ra_id: str = Field(serialization_alias="raId")
    ra_name: str = Field(serialization_alias="raName")
    pressure_score: int = Field(serialization_alias="pressureScore")
    event_count: int = Field(serialization_alias="eventCount")
    top_topic: OperationalTopic = Field(serialization_alias="topTopic")
    trend: Trend


class AttentionUnitOut(_CamelModel):
    unit_id: str = Field(serialization_alias="unitId")
    name: str
    ra_name: str = Field(serialization_alias="raName")
    attention_score: int = Field(serialization_alias="attentionScore")
    severity: Severity
    reason: str
    growth_pct: float = Field(serialization_alias="growthPct")
    event_count_24h: int = Field(serialization_alias="eventCount24h")


class TimeSeriesPointOut(_CamelModel):
    ts: datetime
    value: int


class TopicSliceOut(_CamelModel):
    topic: OperationalTopic
    count: int
    pct: float


class AlertEventOut(_CamelModel):
    id: str
    rule_name: str = Field(serialization_alias="ruleName")
    severity: Severity
    triggered_at: datetime = Field(serialization_alias="triggeredAt")
    scope: str
    message: str
    status: AlertStatus


class PipelineHealthOut(_CamelModel):
    status: HealthStatus
    latency_p95_seconds: float = Field(serialization_alias="latencyP95Seconds")
    threshold_seconds: float = Field(serialization_alias="thresholdSeconds")
    last_successful_ingestion_at: datetime = Field(
        serialization_alias="lastSuccessfulIngestionAt"
    )
    message: str | None = None


class _ItemsEnvelope(_CamelModel):
    """Generic ``{"items": [...]}`` envelope used by collection endpoints."""


class KPIList(_ItemsEnvelope):
    items: list[KPIOut]


class RegionPressureList(_ItemsEnvelope):
    items: list[RegionPressureOut]


class AttentionUnitList(_ItemsEnvelope):
    items: list[AttentionUnitOut]


class TimeSeriesList(_ItemsEnvelope):
    items: list[TimeSeriesPointOut]


class TopicSliceList(_ItemsEnvelope):
    items: list[TopicSliceOut]


class AlertEventList(_ItemsEnvelope):
    items: list[AlertEventOut]
