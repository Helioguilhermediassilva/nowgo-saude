"""End-to-end test of the JWT auth backend via the real FastAPI app (T028).

The default test runtime keeps ``auth_backend=static`` so the rest of the
suite stays untouched. This module flips the backend to ``jwt`` inside a
scoped fixture (env vars + cache reset) and verifies that:

1. A valid JWT with the ``admin`` role authenticates against an admin endpoint.
2. A JWT lacking the required role yields 403 (not 401).
3. A JWT signed with the wrong secret yields 401.
4. An absent ``Authorization`` header yields 401.

We never reuse the project-wide ``client`` fixture here because that fixture
relies on the cached ``Settings`` snapshot built at import time.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt

JWT_SECRET = "integration-test-secret"  # noqa: S105 (test fixture, not a real credential)
JWT_ALG = "HS256"
JWT_ISS = "nowgo-saude-test"
JWT_AUD = "nowgo-saude-backend"


def _issue(sub: str, roles: list[str], *, secret: str = JWT_SECRET) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": sub,
            "iss": JWT_ISS,
            "aud": JWT_AUD,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "roles": roles,
        },
        secret,
        algorithm=JWT_ALG,
    )


@pytest.fixture
def jwt_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Spin up the app with ``auth_backend=jwt`` for this test only."""
    monkeypatch.setenv("NOWGO_AUTH_BACKEND", "jwt")
    monkeypatch.setenv("NOWGO_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("NOWGO_JWT_ALGORITHM", JWT_ALG)
    monkeypatch.setenv("NOWGO_JWT_ISSUER", JWT_ISS)
    monkeypatch.setenv("NOWGO_JWT_AUDIENCE", JWT_AUD)

    from nowgo_saude import db
    from nowgo_saude.config import get_settings
    from nowgo_saude.core.auth.factory import reset_auth_provider_cache
    from nowgo_saude.main import create_app

    # Invalidate snapshots built under ``auth_backend=static``.
    get_settings.cache_clear()
    reset_auth_provider_cache()

    db.Base.metadata.drop_all(bind=db.engine)
    db.init_db()
    app = create_app()
    with TestClient(app) as tc:
        yield tc

    # Restore defaults so the rest of the suite resumes on the static backend.
    get_settings.cache_clear()
    reset_auth_provider_cache()


def test_valid_jwt_authenticates_admin(jwt_client: TestClient) -> None:
    token = _issue(sub="user-admin", roles=["admin"])
    r = jwt_client.get(
        "/api/v1/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text


def test_jwt_missing_role_yields_403(jwt_client: TestClient) -> None:
    # Authenticates fine but the ``analyst`` role is not ``admin``.
    token = _issue(sub="user-analyst", roles=["analyst"])
    r = jwt_client.get(
        "/api/v1/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert "admin" in r.json()["detail"]


def test_jwt_bad_signature_yields_401(jwt_client: TestClient) -> None:
    token = _issue(sub="forger", roles=["admin"], secret="wrong-secret")
    r = jwt_client.get(
        "/api/v1/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401


def test_missing_authorization_header_yields_401(jwt_client: TestClient) -> None:
    r = jwt_client.get("/api/v1/sources")
    assert r.status_code == 401
