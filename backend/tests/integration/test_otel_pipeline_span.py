"""Integration test: the ingestion pipeline emits a span with rich attributes.

Validates that T040 (OTel wiring) reaches the domain layer end-to-end. We do
NOT enable ``otel_enabled`` in Settings — instead we call ``setup_tracing``
directly with an in-memory exporter so the test stays self-contained and
deterministic (no OTLP collector required).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from nowgo_saude.core.observability.otel import setup_tracing, shutdown_tracing

HEADERS = {"Authorization": "Bearer test-admin-token"}


@pytest.fixture
def span_exporter():
    """Attach an in-memory exporter to whatever TracerProvider is active."""
    exporter = InMemorySpanExporter()
    setup_tracing(exporter=exporter)
    yield exporter
    shutdown_tracing()


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
        headers=HEADERS,
    )


def test_ingest_event_emits_pipeline_span(
    client: TestClient, span_exporter: InMemorySpanExporter
) -> None:
    """Posting an event yields a ``pipeline.ingest_event`` span with attributes."""
    _create_source(client)

    response = client.post(
        "/api/v1/events",
        json={
            "source_slug": "ouvidor_sus_df",
            "external_id": "OTEL-1",
            "region_code": "5300108",
            "topic": "acesso_consulta",
            "sentiment": -1,
            "severity": 2,
            "confidence": 0.9,
            "text": "Atraso no atendimento na UBS.",
            "iso_37120": ["15.1"],
            "iso_37122": [],
        },
        headers=HEADERS,
    )
    assert response.status_code == 201, response.text

    pipeline_spans = [
        s for s in span_exporter.get_finished_spans() if s.name == "pipeline.ingest_event"
    ]
    assert len(pipeline_spans) == 1
    span = pipeline_spans[0]
    assert span.attributes["nowgo.source.slug"] == "ouvidor_sus_df"
    assert span.attributes["nowgo.event.topic"] == "acesso_consulta"
    assert span.attributes["nowgo.event.status"] == "classified"
    assert span.attributes["nowgo.event.severity"] == 2
    assert span.attributes["nowgo.anonymization.failed"] is False


def test_low_confidence_attribute_reflects_downgrade(
    client: TestClient, span_exporter: InMemorySpanExporter
) -> None:
    """Severity attribute carries the post-rule value (FR-003 downgrade)."""
    _create_source(client)

    response = client.post(
        "/api/v1/events",
        json={
            "source_slug": "ouvidor_sus_df",
            "region_code": "5300108",
            "topic": "acesso_consulta",
            "sentiment": -1,
            "severity": 2,
            "confidence": 0.3,
            "text": "Texto qualquer.",
            "iso_37120": [],
            "iso_37122": [],
        },
        headers=HEADERS,
    )
    assert response.status_code == 201

    pipeline_spans = [
        s for s in span_exporter.get_finished_spans() if s.name == "pipeline.ingest_event"
    ]
    assert len(pipeline_spans) == 1
    # Severity was downgraded from 2 → 1 because confidence < threshold (0.6).
    assert pipeline_spans[0].attributes["nowgo.event.severity"] == 1
