"""Unit tests for the OTel bootstrap (T040).

The tests exercise :func:`setup_tracing` in isolation using an in-memory
exporter. They MUST NOT depend on the OTLP collector being reachable — every
CI environment runs without it.
"""

from __future__ import annotations

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from nowgo_saude.core.observability import otel as otel_module
from nowgo_saude.core.observability.otel import setup_tracing, shutdown_tracing


@pytest.fixture(autouse=True)
def _reset_provider():
    """OTel's global tracer provider is write-once per process; we can only
    reset our own module-level reference between tests. The first test in the
    process seats the provider; subsequent tests reuse it via the
    add-processor branch in :func:`setup_tracing`."""
    yield
    shutdown_tracing()


def test_setup_tracing_disabled_returns_none():
    """When ``enabled=False`` no provider is installed and we exit cleanly."""
    assert setup_tracing(enabled=False) is None
    assert otel_module._provider is None


def test_setup_tracing_emits_spans_via_custom_exporter():
    """Spans created after setup are captured by an injected exporter."""
    exporter = InMemorySpanExporter()
    provider = setup_tracing(service_name="test-service", exporter=exporter)
    assert provider is not None

    tracer = trace.get_tracer("nowgo_saude.test")
    with tracer.start_as_current_span("unit.smoke") as span:
        span.set_attribute("test.attr", "ok")

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "unit.smoke"
    assert spans[0].attributes["test.attr"] == "ok"
    # Resource always carries *some* service.name so collectors can route it.
    # We do not assert the exact value here: OTel's global TracerProvider is
    # write-once per process, so if a previous test (in the same suite run)
    # already seated the provider, our ``service_name="test-service"`` will be
    # ignored. The write-once semantics are covered explicitly by
    # ``test_setup_tracing_attaches_additional_exporter_on_resetup``.
    assert "service.name" in spans[0].resource.attributes


def test_setup_tracing_attaches_additional_exporter_on_resetup():
    """A second call keeps the existing provider and attaches the new exporter
    (OTel's global is write-once, so this is the only safe semantics)."""
    exporter_a = InMemorySpanExporter()
    provider_a = setup_tracing(service_name="svc-a", exporter=exporter_a)

    exporter_b = InMemorySpanExporter()
    provider_b = setup_tracing(service_name="svc-b", exporter=exporter_b)

    # Same underlying provider — no global replacement attempted.
    assert provider_a is provider_b

    tracer = trace.get_tracer("nowgo_saude.test")
    with tracer.start_as_current_span("multi-exporter"):
        pass

    # Both exporters receive the span because both processors stayed attached.
    assert len(exporter_a.get_finished_spans()) == 1
    assert len(exporter_b.get_finished_spans()) == 1


def test_shutdown_clears_module_provider():
    setup_tracing(exporter=InMemorySpanExporter())
    assert otel_module._provider is not None
    shutdown_tracing()
    assert otel_module._provider is None
