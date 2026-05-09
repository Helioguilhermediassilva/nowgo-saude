"""Unit tests for the PII vault encryption service."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from nowgo_saude.models.audit_entry import AuditEntry
from nowgo_saude.models.pii_vault import PIIVaultRecord
from nowgo_saude.services import pii_vault as pii_vault_service


def test_store_encrypts_and_persists_record(db_session: Session) -> None:
    record = pii_vault_service.store(
        db_session, token="pii:cpf:abc123", category="cpf", value="123.456.789-00"
    )
    db_session.commit()

    persisted = db_session.get(PIIVaultRecord, "pii:cpf:abc123")
    assert persisted is not None
    assert persisted.category == "cpf"
    assert persisted.key_version >= 1
    assert len(persisted.value_iv) == 12
    assert b"123.456.789-00" not in bytes(persisted.value_ciphertext)
    assert record.usage_count == 1


def test_store_is_idempotent_for_same_token(db_session: Session) -> None:
    pii_vault_service.store(
        db_session, token="pii:email:dup", category="email", value="x@y.com"
    )
    db_session.commit()
    pii_vault_service.store(
        db_session, token="pii:email:dup", category="email", value="x@y.com"
    )
    db_session.commit()

    record = db_session.get(PIIVaultRecord, "pii:email:dup")
    assert record is not None
    assert record.usage_count == 2


def test_reidentify_returns_plaintext_and_audits(db_session: Session) -> None:
    pii_vault_service.store(
        db_session, token="pii:phone:t1", category="phone", value="(61) 99999-1234"
    )
    db_session.commit()

    result = pii_vault_service.reidentify(
        db_session, "pii:phone:t1", actor_id="officer-1", reason="court order #42"
    )
    db_session.commit()

    assert result.value == "(61) 99999-1234"
    assert result.category == "phone"
    assert result.usage_count == 2  # store=1 + reidentify=2

    audit_rows = db_session.query(AuditEntry).filter_by(action="pii.reidentify").all()
    assert len(audit_rows) == 1
    assert audit_rows[0].target_id == "pii:phone:t1"
    assert audit_rows[0].actor_role == "lgpd_officer"


def test_reidentify_unknown_token_raises(db_session: Session) -> None:
    with pytest.raises(pii_vault_service.VaultError):
        pii_vault_service.reidentify(
            db_session, "pii:cpf:missing", actor_id="officer-1", reason="lookup"
        )


def test_unsupported_category_rejected(db_session: Session) -> None:
    with pytest.raises(pii_vault_service.VaultError):
        pii_vault_service.store(
            db_session, token="pii:foo:bar", category="passport", value="X"
        )
