"""Unit tests for egress_guard (T042).

Validates Constitution Principles I (Sovereignty) and II (LGPD by Design) at
the network boundary: every outbound payload is re-scanned for PII and every
target hostname is checked against the allowlist.
"""

from __future__ import annotations

import pytest

from nowgo_saude.core.llm.egress_guard import (
    EgressDecision,
    EgressViolationError,
    assert_safe,
    inspect,
)

ALLOW = ["api.x.ai", "api.openai.com"]


def test_allowed_host_with_clean_payload_passes() -> None:
    decision = inspect("https://api.x.ai/v1/chat", "Cidadão relata fila longa.", allowlist=ALLOW)
    assert decision.allowed is True
    assert decision.kind == "allowed"
    assert decision.hostname == "api.x.ai"


def test_assert_safe_does_not_raise_on_allowed_decision() -> None:
    assert_safe("https://api.x.ai/v1/chat", "Texto operacional.", allowlist=ALLOW)


def test_host_outside_allowlist_is_blocked() -> None:
    decision = inspect("https://evil.example.com/data", "ok", allowlist=ALLOW)
    assert decision.allowed is False
    assert decision.kind == "host_not_allowed"
    assert decision.hostname == "evil.example.com"


def test_assert_safe_raises_on_host_outside_allowlist() -> None:
    with pytest.raises(EgressViolationError) as exc_info:
        assert_safe("https://evil.example.com/v1", "clean", allowlist=ALLOW)
    err = exc_info.value
    assert err.kind == "host_not_allowed"
    assert err.hostname == "evil.example.com"


def test_pii_residue_is_blocked_even_on_allowed_host() -> None:
    text_with_cpf = "Reclamação do cidadão 123.456.789-09 sobre atendimento."
    decision = inspect("https://api.x.ai/v1/chat", text_with_cpf, allowlist=ALLOW)
    assert decision.allowed is False
    assert decision.kind == "pii_residue"
    assert decision.hostname == "api.x.ai"


def test_assert_safe_raises_on_pii_residue() -> None:
    with pytest.raises(EgressViolationError) as exc_info:
        assert_safe(
            "https://api.x.ai/v1/chat",
            "Email do usuário: joao@example.com",
            allowlist=ALLOW,
        )
    assert exc_info.value.kind == "pii_residue"


def test_bare_hostname_is_accepted_as_target() -> None:
    """Adapters that already split URL parts can pass the hostname directly."""
    decision = inspect("api.x.ai", "clean", allowlist=ALLOW)
    assert decision.allowed is True
    assert decision.hostname == "api.x.ai"


def test_empty_target_is_blocked() -> None:
    decision = inspect("", "clean", allowlist=ALLOW)
    assert decision.allowed is False
    assert decision.kind == "host_not_allowed"


def test_hostname_match_is_case_insensitive() -> None:
    decision = inspect("https://API.X.AI/v1", "clean", allowlist=["api.x.ai"])
    assert decision.allowed is True
    assert decision.hostname == "api.x.ai"


def test_allowlist_entries_are_normalized() -> None:
    decision = inspect("https://api.x.ai/v1", "clean", allowlist=["  Api.X.Ai  "])
    assert decision.allowed is True


def test_empty_payload_is_treated_as_safe() -> None:
    """A health probe with no body MUST be allowed if hostname is allowed."""
    decision = inspect("https://api.x.ai/health", "", allowlist=ALLOW)
    assert decision.allowed is True


def test_decision_is_frozen() -> None:
    decision = inspect("https://api.x.ai/v1", "ok", allowlist=ALLOW)
    with pytest.raises((AttributeError, Exception)):
        decision.allowed = False  # type: ignore[misc]


def test_assert_safe_uses_settings_allowlist_when_none_passed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default-arg path: read allowlist from get_settings() at call time."""
    from nowgo_saude.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "nowgo_saude.config.get_settings",
        lambda: Settings(egress_allowlist=["api.x.ai"]),
    )
    assert_safe("https://api.x.ai/v1", "clean")
    with pytest.raises(EgressViolationError):
        assert_safe("https://other.com/v1", "clean")


def test_decision_object_returned_is_correct_type() -> None:
    decision = inspect("https://api.x.ai/v1", "clean", allowlist=ALLOW)
    assert isinstance(decision, EgressDecision)
