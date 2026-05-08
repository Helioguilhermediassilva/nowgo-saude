"""AuditEntry model: append-only ledger for sensitive actions (LGPD-relevant)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuditEntry(Base):
    __tablename__ = "audit_entries"
    __table_args__ = (
        Index("idx_audit_at", "at"),
        Index("idx_audit_target", "target_kind", "target_id"),
        Index("idx_audit_actor", "actor_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    audit_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    prev_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
