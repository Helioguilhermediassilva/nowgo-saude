"""Source model: configured ingestion endpoints (ouvidoria, social, internal)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

SOURCE_KINDS = ("ouvidoria_oficial", "social_publica", "formulario_interno")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('ouvidoria_oficial','social_publica','formulario_interno')",
            name="ck_sources_kind",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    retention_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    iso_37120_default: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    events: Mapped[list[TelemetryEvent]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="source", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[list[PipelineRun]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="source", cascade="all, delete-orphan"
    )
