"""Integration tests for the PII re-identification API."""

from __future__ import annotations

from fastapi.testclient import TestClient

ADMIN_HEADERS = {"Authorization": "Bearer test-admin-token"}
LGPD_HEADERS = {"Authorization": "Bearer test-lgpd-officer-token"}


def _create_source(client: TestClient) -> None:
    client.post(
        "/api/v1/sources",
        json={
            "slug": "ouvidor_sus_df",
            "kind": "ouvidoria_oficial",
            "display_name": "OuvidorSUS DF",
            "config": {},
            "retention_policy": {"event_days": 365, "pii_days": 30, "raw_days": 7},
            "iso_37120_default": [],
        },
        headers=ADMIN_HEADERS,
    )


def _ingest_with_pii(client: TestClient) -> dict:
    payload = {
        "source_slug": "ouvidor_sus_df",
        "external_id": "OSDF-PII-1",
        "region_code": "5300108",
        "topic": "acesso_consulta",
        "sentiment": -1,
        "severity": 2,
        "confidence": 0.9,
        "text": "Paciente com CPF 123.456.789-00 e telefone (61) 99999-1234.",
        "iso_37120": ["15.1"],
        "iso_37122": [],
    }
    r = client.post("/api/v1/events", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 201, r.text
    return r.json()


def test_reidentify_returns_original_value(client: TestClient) -> None:
    _create_source(client)
    event = _ingest_with_pii(client)
    cpf_token = next(t for t in event["pii_tokens"] if t.startswith("pii:cpf:"))

    r = client.post(
        f"/api/v1/pii/{cpf_token}",
        json={"reason": "investigação de duplicidade"},
        headers=LGPD_HEADERS,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token"] == cpf_token
    assert body["category"] == "cpf"
    assert body["value"] == "123.456.789-00"
    assert body["key_version"] >= 1
    assert body["usage_count"] >= 2


def test_reidentify_requires_lgpd_token(client: TestClient) -> None:
    _create_source(client)
    event = _ingest_with_pii(client)
    token = event["pii_tokens"][0]

    # Admin token must NOT be accepted on the PII endpoint
    r = client.post(
        f"/api/v1/pii/{token}",
        json={"reason": "test"},
        headers=ADMIN_HEADERS,
    )
    assert r.status_code == 401

    # No auth at all
    r = client.post(f"/api/v1/pii/{token}", json={"reason": "test"})
    assert r.status_code == 401


def test_reidentify_unknown_token_returns_404(client: TestClient) -> None:
    r = client.post(
        "/api/v1/pii/pii:cpf:doesnotexist",
        json={"reason": "ghost"},
        headers=LGPD_HEADERS,
    )
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "token_not_found"


def test_reidentify_requires_reason(client: TestClient) -> None:
    _create_source(client)
    event = _ingest_with_pii(client)
    token = event["pii_tokens"][0]

    r = client.post(f"/api/v1/pii/{token}", json={}, headers=LGPD_HEADERS)
    assert r.status_code == 422
