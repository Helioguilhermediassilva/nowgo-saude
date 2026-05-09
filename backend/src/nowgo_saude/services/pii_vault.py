"""PII Vault service: AES-GCM encryption keyed by anonymizer tokens.

Encryption uses AES-256-GCM via cryptography.hazmat. The key is loaded from
``Settings.pii_vault_key`` (base64-encoded 32 bytes) and tagged with
``Settings.pii_vault_key_version`` so we can rotate keys without losing access
to historical ciphertext (rotation = bump version, keep old key resolvable via
``_PREVIOUS_KEYS`` env in a future iteration).

The vault is an upsert table: re-seeing the same value (same anonymizer token)
increments ``usage_count`` and updates ``last_seen_at`` without re-encrypting.
"""

from __future__ import annotations

import base64
import os
from datetime import UTC, datetime
from typing import NamedTuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models.pii_vault import PII_CATEGORIES, PIIVaultRecord
from . import audit as audit_service

_NONCE_SIZE = 12  # NIST-recommended IV size for AES-GCM


class VaultError(Exception):
    """Raised when the vault key is misconfigured or a token cannot be decrypted."""


class ReidentifiedValue(NamedTuple):
    token: str
    category: str
    value: str
    key_version: int
    first_seen_at: datetime
    last_seen_at: datetime
    usage_count: int


def _load_key() -> tuple[bytes, int]:
    settings = get_settings()
    try:
        key = base64.b64decode(settings.pii_vault_key)
    except (ValueError, TypeError) as exc:
        raise VaultError("pii_vault_key is not valid base64") from exc
    if len(key) != 32:
        raise VaultError(
            f"pii_vault_key must decode to 32 bytes for AES-256-GCM, got {len(key)}"
        )
    return key, settings.pii_vault_key_version


def store(session: Session, *, token: str, category: str, value: str) -> PIIVaultRecord:
    """Insert or update the encrypted PII record for ``token``.

    Returns the persisted row. Idempotent: identical (token, value) pairs are
    not re-encrypted; only ``last_seen_at`` and ``usage_count`` are bumped.
    """
    if category not in PII_CATEGORIES:
        raise VaultError(f"unsupported PII category: {category}")
    if not token or not value:
        raise VaultError("token and value must be non-empty")

    record = session.get(PIIVaultRecord, token)
    if record is not None:
        record.last_seen_at = datetime.now(UTC)
        record.usage_count = (record.usage_count or 0) + 1
        return record

    key, version = _load_key()
    iv = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(iv, value.encode("utf-8"), token.encode("utf-8"))
    record = PIIVaultRecord(
        token=token,
        category=category,
        value_ciphertext=ciphertext,
        value_iv=iv,
        key_version=version,
    )
    session.add(record)
    session.flush()
    return record


def reidentify(
    session: Session,
    token: str,
    *,
    actor_id: str,
    actor_role: str = "lgpd_officer",
    reason: str | None = None,
) -> ReidentifiedValue:
    """Decrypt the vault record for ``token`` and emit an immutable audit entry.

    The audit row carries no plaintext: only the token (already a hash) and a
    free-form reason supplied by the caller.
    """
    record = session.get(PIIVaultRecord, token)
    if record is None:
        raise VaultError(f"unknown vault token: {token}")

    key, _ = _load_key()
    try:
        plaintext = AESGCM(key).decrypt(
            bytes(record.value_iv),
            bytes(record.value_ciphertext),
            token.encode("utf-8"),
        )
    except Exception as exc:
        raise VaultError("ciphertext authentication failed") from exc

    record.last_seen_at = datetime.now(UTC)
    record.usage_count = (record.usage_count or 0) + 1
    audit_service.record(
        session,
        actor_id=actor_id,
        actor_role=actor_role,
        action="pii.reidentify",
        target_kind="pii_record",
        target_id=token,
        payload={"reason": reason} if reason else None,
        metadata={"category": record.category, "key_version": record.key_version},
    )
    return ReidentifiedValue(
        token=token,
        category=record.category,
        value=plaintext.decode("utf-8"),
        key_version=record.key_version,
        first_seen_at=record.first_seen_at,
        last_seen_at=record.last_seen_at,
        usage_count=record.usage_count,
    )
