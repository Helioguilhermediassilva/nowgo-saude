"""Pydantic v2 schemas mirroring the OpenAPI ingestion API contract."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SourceKind = Literal["ouvidoria_oficial", "social_publica", "formulario_interno"]
RunStatus = Literal["running", "succeeded", "partial", "failed"]
EventStatus = Literal["classified", "quarantined", "reprocessing"]

SlugStr = Annotated[str, Field(pattern=r"^[a-z0-9_]+$", min_length=1, max_length=64)]


class RetentionPolicy(BaseModel):
    event_days: int = Field(ge=1)
    pii_days: int = Field(ge=0)
    raw_days: int = Field(ge=0)


class SourceBase(BaseModel):
    slug: SlugStr
    kind: SourceKind
    display_name: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    retention_policy: RetentionPolicy
    iso_37120_default: list[str] = Field(default_factory=list)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool | None = None
    display_name: str | None = None
    config: dict[str, Any] | None = None
    retention_policy: RetentionPolicy | None = None


class SourceOut(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class PipelineRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    started_at: datetime
    finished_at: datetime | None = None
    status: RunStatus
    events_collected: int = 0
    events_quarantined: int = 0
    error_summary: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)


class ReprocessRequest(BaseModel):
    event_ids: list[str] = Field(min_length=1, max_length=1000)
    reason: str | None = Field(default=None, max_length=500)


class ReprocessResponse(BaseModel):
    pipeline_run_id: str
    enqueued: int


class MetricsSummary(BaseModel):
    events_per_minute: float
    p95_latency_ms: float
    dlq_depth: int
    anonymization_failures_24h: int
    updated_at: datetime


class EventIngestRequest(BaseModel):
    """Raw ingestion payload accepted by the pipeline (pre-anonymization)."""

    source_slug: SlugStr
    external_id: str | None = None
    occurred_at: datetime | None = None
    region_code: str = Field(pattern=r"^[0-9]{7}$")
    unit_code: str | None = None
    topic: str = Field(min_length=1, max_length=64)
    subtopic: str | None = Field(default=None, max_length=64)
    sentiment: int = Field(ge=-2, le=2)
    severity: int = Field(ge=0, le=3)
    confidence: float = Field(ge=0.0, le=1.0)
    text: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    iso_37120: list[str] = Field(default_factory=list)
    iso_37122: list[str] = Field(default_factory=list)

    @field_validator("iso_37120")
    @classmethod
    def _validate_iso_37120(cls, value: list[str]) -> list[str]:
        import re

        pattern = re.compile(r"^15\.[0-9]{1,2}$")
        for code in value:
            if not pattern.match(code):
                raise ValueError(f"invalid ISO 37120 code: {code!r}")
        return value


class TelemetryEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_slug: str
    external_id: str | None = None
    received_at: datetime
    occurred_at: datetime | None = None
    region_code: str
    unit_code: str | None = None
    topic: str
    subtopic: str | None = None
    sentiment: int
    severity: int
    confidence: float
    text_anonymized: str
    pii_tokens: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    iso_37120: list[str] = Field(default_factory=list)
    iso_37122: list[str] = Field(default_factory=list)
    status: EventStatus


class PiiReidentifyRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class PiiReidentifyResponse(BaseModel):
    token: str
    category: Literal["cpf", "cns", "name", "email", "phone", "address"]
    value: str
    key_version: int
    first_seen_at: datetime
    last_seen_at: datetime
    usage_count: int


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
