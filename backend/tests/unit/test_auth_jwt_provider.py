"""Unit tests for :class:`JwtAuthProvider` (T028).

Covers the supported algorithm (HS256), the standard claim checks, and the
project-specific ``roles`` / ``lgpd_authorized`` claims. We deliberately do
NOT mock ``python-jose`` — the test signs real tokens with the same secret
so the assertion exercises the real signature path.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from jose import jwt

from nowgo_saude.core.auth import AuthError, JwtAuthProvider

SECRET = "test-secret"  # noqa: S105 (test fixture, not a real credential)
ALG = "HS256"
ISS = "nowgo-saude-test"
AUD = "nowgo-saude-backend"


def _issue(**overrides: Any) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": "user-42",
        "iss": ISS,
        "aud": AUD,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "roles": ["admin"],
    }
    claims.update(overrides)
    # ``None`` means "omit this claim entirely" \u2014 python-jose validates types
    # on the claim values present in the payload, so leaving ``sub=None`` in
    # would trigger jose's own error before ours.
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, SECRET, algorithm=ALG)


@pytest.fixture
def provider() -> JwtAuthProvider:
    return JwtAuthProvider(secret=SECRET, algorithm=ALG, issuer=ISS, audience=AUD)


def test_valid_token_yields_principal(provider: JwtAuthProvider) -> None:
    principal = provider.authenticate(f"Bearer {_issue()}")
    assert principal.subject == "user-42"
    assert principal.roles == ("admin",)
    assert principal.lgpd_authorized is False


def test_lgpd_claim_is_propagated(provider: JwtAuthProvider) -> None:
    token = _issue(roles=["lgpd_officer"], lgpd_authorized=True)
    principal = provider.authenticate(f"Bearer {token}")
    assert principal.has_role("lgpd_officer")
    assert principal.lgpd_authorized is True


def test_multiple_roles_preserved(provider: JwtAuthProvider) -> None:
    token = _issue(roles=["admin", "operator"])
    principal = provider.authenticate(f"Bearer {token}")
    assert principal.roles == ("admin", "operator")


def test_expired_token_raises(provider: JwtAuthProvider) -> None:
    past = datetime.now(UTC) - timedelta(minutes=1)
    token = _issue(exp=int(past.timestamp()))
    with pytest.raises(AuthError, match="expired"):
        provider.authenticate(f"Bearer {token}")


def test_wrong_audience_raises(provider: JwtAuthProvider) -> None:
    token = _issue(aud="other-service")
    with pytest.raises(AuthError, match="invalid token"):
        provider.authenticate(f"Bearer {token}")


def test_wrong_issuer_raises(provider: JwtAuthProvider) -> None:
    token = _issue(iss="rogue-idp")
    with pytest.raises(AuthError, match="invalid token"):
        provider.authenticate(f"Bearer {token}")


def test_bad_signature_raises(provider: JwtAuthProvider) -> None:
    token = jwt.encode(
        {
            "sub": "u",
            "iss": ISS,
            "aud": AUD,
            "exp": int((datetime.now(UTC) + timedelta(minutes=1)).timestamp()),
        },
        "wrong-secret",
        algorithm=ALG,
    )
    with pytest.raises(AuthError, match="invalid token"):
        provider.authenticate(f"Bearer {token}")


def test_missing_sub_raises(provider: JwtAuthProvider) -> None:
    token = _issue(sub=None)
    with pytest.raises(AuthError, match="missing 'sub' claim"):
        provider.authenticate(f"Bearer {token}")


def test_roles_not_list_raises(provider: JwtAuthProvider) -> None:
    token = _issue(roles="admin")  # string instead of list
    with pytest.raises(AuthError, match="must be a list of strings"):
        provider.authenticate(f"Bearer {token}")


def test_missing_roles_claim_defaults_to_empty(provider: JwtAuthProvider) -> None:
    """Tokens without ``roles`` authenticate but carry no roles (RBAC rejects)."""
    token = jwt.encode(
        {
            "sub": "u",
            "iss": ISS,
            "aud": AUD,
            "exp": int((datetime.now(UTC) + timedelta(minutes=1)).timestamp()),
        },
        SECRET,
        algorithm=ALG,
    )
    principal = provider.authenticate(f"Bearer {token}")
    assert principal.roles == ()


def test_missing_header_raises(provider: JwtAuthProvider) -> None:
    with pytest.raises(AuthError, match="missing or malformed"):
        provider.authenticate(None)


def test_non_bearer_scheme_raises(provider: JwtAuthProvider) -> None:
    with pytest.raises(AuthError, match="missing or malformed"):
        provider.authenticate("Token abc.def.ghi")
