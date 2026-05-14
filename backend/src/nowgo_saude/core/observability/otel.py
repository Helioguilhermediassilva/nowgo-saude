"""OpenTelemetry bootstrap for the FastAPI backend (T040).

Single source of truth for tracing setup. The OTLP endpoint and service name
are sourced from the standard ``OTEL_*`` environment variables (the SDK reads
them natively) so the backend interoperates with the otel-collector defined
in ``infra/docker/docker-compose.dev.yaml`` without project-specific glue.

Tests inject an in-memory ``SpanExporter`` via the ``exporter`` argument to
assert on span emission without touching the network. Production callers leave
``exporter=None`` and the OTLP HTTP exporter is configured automatically.

Constitution Principle VII (Observability): every long-lived service must emit
spans for its critical paths so SREs can debug without re-reading code.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter

if TYPE_CHECKING:
    from fastapi import FastAPI

_DEFAULT_SERVICE_NAME = "nowgo-saude-backend"
_provider: TracerProvider | None = None


def setup_tracing(
    app: FastAPI | None = None,
    *,
    service_name: str | None = None,
    exporter: SpanExporter | None = None,
    enabled: bool = True,
) -> TracerProvider | None:
    """Initialise the global tracer provider and instrument FastAPI.

    Idempotent: a second call replaces the previous provider so tests can
    isolate state. When ``enabled=False`` we install a noop tracer provider
    (already the OTel default) and return ``None``.

    Parameters
    ----------
    app:
        FastAPI application to instrument. ``None`` skips ASGI instrumentation
        (useful for worker processes or unit tests that only need the SDK).
    service_name:
        Overrides ``OTEL_SERVICE_NAME``. Defaults to the env var or
        ``"nowgo-saude-backend"``.
    exporter:
        Custom :class:`SpanExporter` (tests inject ``InMemorySpanExporter``).
        When ``None`` we wire :class:`OTLPSpanExporter` which reads
        ``OTEL_EXPORTER_OTLP_ENDPOINT`` from the environment.
    enabled:
        When ``False`` skip all setup and return ``None``. Lets callers gate
        OTel on a Settings flag without branching at the call site.
    """
    global _provider

    if not enabled:
        return None

    # In-memory exporters need SimpleSpanProcessor so spans are flushed
    # synchronously and visible to assertions immediately after the call.
    if exporter is None:
        processor: BatchSpanProcessor | SimpleSpanProcessor = BatchSpanProcessor(
            OTLPSpanExporter()
        )
    else:
        processor = SimpleSpanProcessor(exporter)

    # OTel's global tracer provider is write-once per process: a second call
    # to ``set_tracer_provider`` is silently rejected. To stay idempotent
    # (tests swap exporters, production may re-bootstrap during reloads) we
    # detect a real ``TracerProvider`` already registered and attach the new
    # processor to it instead of creating an orphan.
    existing = trace.get_tracer_provider()
    if isinstance(existing, TracerProvider):
        existing.add_span_processor(processor)
        _provider = existing
    else:
        name = service_name or os.environ.get("OTEL_SERVICE_NAME") or _DEFAULT_SERVICE_NAME
        resource = Resource.create({SERVICE_NAME: name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _provider = provider

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)

    return _provider


def shutdown_tracing() -> None:
    """Flush pending spans and clear our module reference.

    We do NOT call ``provider.shutdown()`` because OTel's global is write-once;
    a hard shutdown would leave the global pointing at an unusable provider
    and break any subsequent ``setup_tracing`` call in the same process.
    Production lifespan ends with process exit, where flushing is implicit.
    """
    global _provider
    if _provider is not None:
        _provider.force_flush()
        _provider = None
