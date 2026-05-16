"""WorkerRun: append-only execution log for every AI worker invocation.

This is the *operational* counterpart to AuditEntry (which records
LGPD-relevant business actions). One row per worker invocation, written
whether the run succeeds, fails, or degrades. Latency, cost, and model
version are first-class columns so the cost monitor (T041) can aggregate
without parsing JSON.

Status semantics
----------------
``success``  — worker produced its expected output (signal, recommendation,
               brief, classification) and persisted it.
``degraded`` — produced output but via fallback path (LLM unreachable,
               guard rejection routed to heuristic, etc).
``failure``  — exception bubbled up; ``error_message`` carries the cause.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...db import Base

WORKER_STATUSES = ("success", "degraded", "failure")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class WorkerRun(Base):
    __tablename__ = "ai_worker_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success','degraded','failure')",
            name="ck_worker_run_status",
        ),
        Index("idx_worker_run_started", "started_at"),
        Index("idx_worker_run_worker_status", "worker_name", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    worker_name: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)

    # Input/output digests — full payloads are NOT stored here to keep the
    # table small. ``input_summary``/``output_summary`` carry the minimum
    # for diffing across runs (e.g. event count, anomaly id, brief date).
    input_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    llm_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # USD with 6 decimal places — Grok pricing today is well below 1 cent
    # per call but the column has to survive a future expensive model.
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
