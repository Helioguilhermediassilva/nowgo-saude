"""SQLAlchemy ORM models for the citizen telemetry ingestion pipeline.

For the MVP we collapse the multi-schema PostgreSQL design described in
data-model.md into a single namespace so the same models work on SQLite
(used in dev/tests) and PostgreSQL (used in prod, where schemas can be
configured via Alembic in a follow-up).
"""

from __future__ import annotations

from .audit_entry import AuditEntry
from .pipeline_run import PipelineRun
from .source import Source
from .telemetry_event import TelemetryEvent

__all__ = ["AuditEntry", "PipelineRun", "Source", "TelemetryEvent"]
