"""HumanDecision: the immutable record of a human acting on a Recommendation.

Append-only by convention (no UPDATE). Each row is the *event* of a
decision — if a reviewer changes their mind they create a new row, so the
audit trail preserves the sequence. Combined with the parent Recommendation's
own ``hitl_status`` (which reflects the *latest* state) this gives us both
the cheap point-query and the full history.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...db import Base

HUMAN_DECISIONS = ("approve", "reject", "edit")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class HumanDecision(Base):
    __tablename__ = "ai_human_decisions"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('approve','reject','edit')",
            name="ck_human_decision_value",
        ),
        Index("idx_human_decision_recommendation", "recommendation_id"),
        Index("idx_human_decision_decided_at", "decided_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recommendation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_recommendations.id", ondelete="CASCADE"),
        nullable=False,
    )
    decided_by: Mapped[str] = mapped_column(String(255), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    # Populated only when ``decision='edit'`` — carries the final, approved
    # text that supersedes ``Recommendation.proposed_action``.
    edited_action: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
