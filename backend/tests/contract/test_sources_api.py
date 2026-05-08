"""Contract tests for /api/v1/sources against the OpenAPI spec."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"Authorization": "Bearer test-admin-token"}


def _retention() -> dict:
    return {"event_days": 365, "pii_days": 30, "raw_days": 7}


def test_create_and_list_sources(client: TestClient) -> None:
    payload = {
        "slug": "ouvidor_sus_df",
        "kind": "ouvidoria_oficial",
        "display_name": "OuvidorSUS DF",
        "config": {"endpoint": "https://example.gov"},
        "retention_policy": _retention(),
        "iso_37120_default": ["15.1"],
    }
    r = client.post("/api/v1/sources", json=payload, headers=HEADERS)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["slug"] == "ouvidor_sus_df"
    assert body["enabled"] is True
    assert body["retention_policy"] == _retention()

    r = client.get("/api/v1/sources", headers=HEADERS)
    assert r.status_code == 200
    items = r.json()
    assert any(s["slug"] == "ouvidor_sus_df" for s in items)


def test_duplicate_slug_returns_409(client: TestClient) -> None:
    payload = {
        "slug": "dup_slug",
        "kind": "social_publica",
        "display_name": "X",
        "config": {},
        "retention_policy": _retention(),
    }
    r1 = client.post("/api/v1/sources", json=payload, headers=HEADERS)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/sources", json=payload, headers=HEADERS)
    assert r2.status_code == 409


def test_unauthenticated_requests_rejected(client: TestClient) -> None:
    r = client.get("/api/v1/sources")
    assert r.status_code == 401


def test_patch_source_disables_it(client: TestClient) -> None:
    payload = {
        "slug": "to_disable",
        "kind": "formulario_interno",
        "display_name": "Form",
        "config": {},
        "retention_policy": _retention(),
    }
    client.post("/api/v1/sources", json=payload, headers=HEADERS)
    r = client.patch(
        "/api/v1/sources/to_disable", json={"enabled": False}, headers=HEADERS
    )
    assert r.status_code == 200
    assert r.json()["enabled"] is False


def test_get_unknown_slug_returns_404(client: TestClient) -> None:
    r = client.get("/api/v1/sources/nope_nope", headers=HEADERS)
    assert r.status_code == 404


def test_invalid_slug_pattern_rejected(client: TestClient) -> None:
    r = client.post(
        "/api/v1/sources",
        json={
            "slug": "Bad Slug!",
            "kind": "ouvidoria_oficial",
            "display_name": "X",
            "config": {},
            "retention_policy": _retention(),
        },
        headers=HEADERS,
    )
    assert r.status_code == 422
