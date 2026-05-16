"""Recommendation: proposed operational action awaiting human review.

Every recommendation is generated **with** an originating
:class:`AnomalySignal` (the recommender is not free-running). The
``hitl_status`` lifecycle is the load-bearing invariant — no action ever
reaches an external system while ``hitl_status='pending'``.

HITL state machine
------------------
``pending``  — produced by the recommender, queued for review.
``approved`` — human OK; downstream workflow may execute the action.
``rejected`` — human discarded; entry retained for feedback loop.
``edited``   — human approved a modified version; ``edited_action`` carries
               the final text used downstream.

The bare-string status mirrors the convention used by
:class:`TelemetryEvent` (string + CheckConstraint) so we stay schema-
portable between SQLite (tests) and PostgreSQL (prod).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...db import Base

HITL_STATUSES = ("pending", "approved", "rejected", "edited")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Recommendation(Base):
    __tablename__ = "ai_recommendations"
    __table_args__ = (
        CheckConstraint(
            "hitl_status IN ('pending','approved','rejected','edited')",
            name="ck_recommendation_hitl_status",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_recommendation_confidence"
        ),
        Index("idx_recommendation_status", "hitl_status"),
        Index("idx_recommendation_created", "created_at"),
        Index("idx_recommendation_anomaly", "anomaly_signal_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    anomaly_signal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_anomaly_signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    proposed_action: Mapped[str] = mapped_column(String, nullable=False)
    justification: Mapped[str] = mapped_column(String, nullable=False)
    # ``evidence`` is a structured bag — typical shape:
    #   {"event_ids": [...], "citations": [...], "kpis": {...}}
    # We keep it as JSON so the recommender can evolve the fields without
    # an Alembic migration; consumers MUST tolerate missing keys.
    evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)

    # Provider attribution (NULL when the recommendation was generated in
    # degraded/heuristic mode after an LLM failover).
    llm_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    hitl_status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # When ``hitl_status='edited'`` the final approved text lives here;
    # ``proposed_action`` is preserved untouched for audit comparison.
    edited_action: Mapped[str | None] = mapped_column(String, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
