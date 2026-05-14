"""Observability plug-point: OpenTelemetry tracing/metrics bootstrap.

The interface :func:`setup_tracing` is the single entrypoint that ``main.py``
calls during the FastAPI lifespan. Tests inject a custom exporter so spans can
be asserted in-memory without needing the OTel collector.
"""

from .otel import setup_tracing, shutdown_tracing

__all__ = ["setup_tracing", "shutdown_tracing"]
