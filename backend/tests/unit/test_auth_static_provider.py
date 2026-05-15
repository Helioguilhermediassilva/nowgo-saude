"""Unit tests for :class:`StaticTokenAuthProvider` (T028).

These pin the dev/CI contract that the rest of the suite relies on: the two
configured tokens map onto deterministic :class:`Principal` shapes, and every
other input raises :class:`AuthError` (never returns an anonymous principal).
"""

from __future__ import annotations

import pytest

from nowgo_saude.core.auth import AuthError, Principal, StaticTokenAuthProvider


@pytest.fixture
def provider() -> StaticTokenAuthProvider:
    return StaticTokenAuthProvider(
        admin_token="admin-tok",
        lgpd_officer_token="lgpd-tok",
    )


def test_admin_token_yields_admin_principal(provider: StaticTokenAuthProvider) -> None:
    principal = provider.authenticate("Bearer admin-tok")
    assert isinstance(principal, Principal)
    assert principal.subject == "admin"
    assert principal.roles == ("admin",)
    assert principal.lgpd_authorized is False
    assert principal.has_role("admin") is True
    assert principal.has_role("lgpd_officer") is False


def test_lgpd_token_yields_lgpd_principal(provider: StaticTokenAuthProvider) -> None:
    principal = provider.authenticate("Bearer lgpd-tok")
    assert principal.subject == "lgpd_officer"
    assert principal.roles == ("lgpd_officer",)
    assert principal.lgpd_authorized is True


def test_missing_header_raises(provider: StaticTokenAuthProvider) -> None:
    with pytest.raises(AuthError, match="missing or malformed"):
        provider.authenticate(None)


def test_empty_header_raises(provider: StaticTokenAuthProvider) -> None:
    with pytest.raises(AuthError, match="missing or malformed"):
        provider.authenticate("")


def test_malformed_scheme_raises(provider: StaticTokenAuthProvider) -> None:
    with pytest.raises(AuthError, match="missing or malformed"):
        provider.authenticate("Basic admin-tok")


def test_unknown_token_raises(provider: StaticTokenAuthProvider) -> None:
    with pytest.raises(AuthError, match="invalid bearer token"):
        provider.authenticate("Bearer totally-wrong")


def test_principal_is_immutable(provider: StaticTokenAuthProvider) -> None:
    """``frozen=True`` dataclass — attribute writes must fail with FrozenInstanceError."""
    from dataclasses import FrozenInstanceError

    principal = provider.authenticate("Bearer admin-tok")
    with pytest.raises(FrozenInstanceError):
        principal.subject = "spoofed"  # type: ignore[misc]
