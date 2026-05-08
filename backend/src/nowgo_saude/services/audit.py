"""Append-only audit logging helper."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.audit_entry import AuditEntry


def _payload_hash(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    serialized = repr(sorted(payload.items())).encode("utf-8")
    return sha256(serialized).hexdigest()


def record(
    session: Session,
    *,
    actor_id: str,
    action: str,
    target_kind: str,
    target_id: str,
    actor_role: str | None = None,
    payload: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEntry:
    """Append an immutable audit entry; returns the persisted row."""
    prev = session.execute(
        select(AuditEntry.payload_hash).order_by(AuditEntry.at.desc()).limit(1)
    ).scalar_one_or_none()
    entry = AuditEntry(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        target_kind=target_kind,
        target_id=target_id,
        payload_hash=_payload_hash(payload),
        audit_metadata=metadata or {},
        prev_hash=prev,
    )
    session.add(entry)
    session.flush()
    return entry
