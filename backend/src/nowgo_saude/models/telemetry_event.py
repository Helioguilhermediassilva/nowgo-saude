"""TelemetryEvent model: canonical anonymized event published downstream."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

EVENT_STATUSES = ("classified", "quarantined", "reprocessing")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_events_source_external"),
        CheckConstraint(
            "status IN ('classified','quarantined','reprocessing')",
            name="ck_events_status",
        ),
        CheckConstraint("sentiment >= -2 AND sentiment <= 2", name="ck_events_sentiment"),
        CheckConstraint("severity >= 0 AND severity <= 3", name="ck_events_severity"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_events_confidence"),
        Index("idx_events_source_received", "source_id", "received_at"),
        Index("idx_events_topic_received", "topic", "received_at"),
        Index("idx_events_region", "region_code"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    region_code: Mapped[str] = mapped_column(String(7), nullable=False)
    unit_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    subtopic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sentiment: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    text_anonymized: Mapped[str] = mapped_column(String, nullable=False)
    pii_tokens: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    iso_37120: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    iso_37122: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    source: Mapped[Source] = relationship(back_populates="events")  # type: ignore[name-defined]  # noqa: F821
