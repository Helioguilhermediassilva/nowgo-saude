"""Integration tests for the end-to-end ingestion pipeline."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"Authorization": "Bearer test-admin-token"}


def _create_source(client: TestClient, slug: str = "ouvidor_sus_df") -> None:
    client.post(
        "/api/v1/sources",
        json={
            "slug": slug,
            "kind": "ouvidoria_oficial",
            "display_name": "OuvidorSUS DF",
            "config": {},
            "retention_policy": {"event_days": 365, "pii_days": 30, "raw_days": 7},
            "iso_37120_default": [],
        },
        headers=HEADERS,
    )


def _ingest_payload(text: str = "Texto sem PII", confidence: float = 0.9) -> dict:
    return {
        "source_slug": "ouvidor_sus_df",
        "external_id": "OSDF-1",
        "region_code": "5300108",
        "topic": "acesso_consulta",
        "sentiment": -1,
        "severity": 2,
        "confidence": confidence,
        "text": text,
        "iso_37120": ["15.1"],
        "iso_37122": [],
    }


def test_event_ingest_classifies_and_audits(client: TestClient) -> None:
    _create_source(client)
    r = client.post(
        "/api/v1/events",
        json=_ingest_payload("Atraso no atendimento na UBS."),
        headers=HEADERS,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "classified"
    assert body["text_anonymized"] == "Atraso no atendimento na UBS."
    assert body["pii_tokens"] == []
    assert body["source_slug"] == "ouvidor_sus_df"


def test_event_with_pii_is_anonymized(client: TestClient) -> None:
    _create_source(client)
    payload = _ingest_payload("Telefone (61) 99999-1234 cliente joao@example.com")
    r = client.post("/api/v1/events", json=payload, headers=HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert "joao@example.com" not in body["text_anonymized"]
    assert "(61) 99999-1234" not in body["text_anonymized"]
    assert any(t.startswith("pii:") for t in body["pii_tokens"])
    assert body["status"] == "classified"


def test_low_confidence_downgrades_severity(client: TestClient) -> None:
    _create_source(client)
    payload = _ingest_payload(confidence=0.4)
    r = client.post("/api/v1/events", json=payload, headers=HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert body["severity"] == 1  # downgraded from 2
    assert body["attributes"].get("low_confidence") is True


def test_unknown_source_returns_422(client: TestClient) -> None:
    r = client.post(
        "/api/v1/events", json=_ingest_payload(text="x"), headers=HEADERS
    )
    assert r.status_code == 422


def test_reprocess_creates_pipeline_run(client: TestClient) -> None:
    _create_source(client)
    ingest = client.post(
        "/api/v1/events", json=_ingest_payload(text="Algo simples"), headers=HEADERS
    )
    event_id = ingest.json()["id"]

    r = client.post(
        "/api/v1/events:reprocess",
        json={"event_ids": [event_id], "reason": "operator review"},
        headers=HEADERS,
    )
    assert r.status_code == 202
    body = r.json()
    assert body["enqueued"] == 1
    assert body["pipeline_run_id"]

    runs = client.get("/api/v1/pipeline-runs", headers=HEADERS).json()
    assert len(runs) >= 1
    assert runs[0]["status"] == "succeeded"


def test_metrics_summary_returns_counts(client: TestClient) -> None:
    _create_source(client)
    client.post("/api/v1/events", json=_ingest_payload(), headers=HEADERS)
    r = client.get("/api/v1/metrics", headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["events_per_minute"] >= 1
    assert "dlq_depth" in body
    assert "anonymization_failures_24h" in body
