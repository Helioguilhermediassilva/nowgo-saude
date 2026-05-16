"""AnomalySignal: statistically-significant deviation in the citizen-telemetry stream.

Produced by the ``anomaly_detector`` worker on a rolling window. The signal
is intentionally *audit-grade*: ``evidence_event_ids`` enumerates every
:class:`TelemetryEvent` that contributed, so the LGPD officer can trace any
downstream Recommendation back to the raw (anonymised) source events.

State machine
-------------
``open`` is the only state a worker may write; the others are flipped by a
human (UI or HITL API) and protected by the AuthProvider's ``analyst`` role.

* ``open``           — fresh from the detector, awaiting review.
* ``acknowledged``   — a human saw it but has not yet acted.
* ``resolved``       — situation handled; metric returned to baseline.
* ``false_positive`` — detector misfired; sample retained for tuning.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...db import Base

ANOMALY_STATUSES = ("open", "acknowledged", "resolved", "false_positive")
SCOPE_KINDS = ("region", "unit", "topic", "global")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AnomalySignal(Base):
    __tablename__ = "ai_anomaly_signals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','acknowledged','resolved','false_positive')",
            name="ck_anomaly_status",
        ),
        CheckConstraint(
            "scope_kind IN ('region','unit','topic','global')",
            name="ck_anomaly_scope_kind",
        ),
        CheckConstraint("severity >= 0 AND severity <= 3", name="ck_anomaly_severity"),
        Index("idx_anomaly_detected_at", "detected_at"),
        Index("idx_anomaly_scope", "scope_kind", "scope_value"),
        Index("idx_anomaly_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    # Window from which the detector consumed evidence — closed-open
    # interval ``[window_start, window_end)``.
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    scope_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    # Free-form value bound by ``scope_kind`` (region_code, unit_code,
    # topic name, or ``"*"`` for ``global``). Kept as plain string instead
    # of an FK so the detector never blocks on dimension-table writes.
    scope_value: Mapped[str] = mapped_column(String(64), nullable=False)

    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    observed: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    # ``deviation_score`` is unit-free (z-score, modified z, or seasonal
    # residual normalised to MAD) so downstream consumers compare across
    # detectors without re-deriving variance.
    deviation_score: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    evidence_event_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
