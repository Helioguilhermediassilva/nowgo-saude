"""PIIVaultRecord model: encrypted lookup of original PII keyed by anonymizer token.

Per data-model.md §3, the vault lives in a segregated schema (`pii_vault`) with
RBAC restricted to LGPD/audit roles. For SQLite parity we keep a single
namespace; on PostgreSQL the schema can be enforced at deploy time. Every read
of this table emits an `AuditEntry` with `action=pii.reidentify`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    LargeBinary,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base

PII_CATEGORIES = ("cpf", "cns", "name", "email", "phone", "address")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class PIIVaultRecord(Base):
    __tablename__ = "pii_vault_records"
    __table_args__ = (
        CheckConstraint(
            "category IN ('cpf','cns','name','email','phone','address')",
            name="ck_pii_vault_category",
        ),
        Index("idx_pii_category", "category"),
        Index("idx_pii_expires_at", "expires_at"),
    )

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    value_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    value_iv: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    usage_count: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
