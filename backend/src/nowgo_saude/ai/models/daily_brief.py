"""DailyBrief: executive summary delivered at 07:00 local time.

One row per business date — ``brief_date`` is unique. Re-running the briefer
overwrites the row in-place (idempotent within the same date) so retries
don't double-deliver. ``degraded_mode=True`` flags that the summary text
was produced by heuristic templates instead of the LLM, per
:class:`DegradedModeBriefer` (T034).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class DailyBrief(Base):
    __tablename__ = "ai_daily_briefs"
    __table_args__ = (
        UniqueConstraint("brief_date", name="uq_daily_brief_date"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    brief_date: Mapped[date] = mapped_column(Date, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Top-N signals/recommendations referenced by ID (not FK — we want the
    # brief to survive a signal being deleted/anonymised after the fact).
    top_signal_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    pending_recommendation_ids: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    # ``kpi_snapshot`` shape (loose by design):
    #   {"complaints_total": int, "sentiment_avg": float, "regions": {...}}
    kpi_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    summary_text: Mapped[str] = mapped_column(String, nullable=False)
    degraded_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    llm_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
