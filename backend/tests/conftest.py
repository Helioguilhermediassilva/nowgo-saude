"""Shared fixtures for contract and integration tests (Feature 001)."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = REPO_ROOT / "specs" / "001-citizen-telemetry-ingestion" / "contracts"

# Configure a per-session sqlite database before any nowgo_saude module is
# imported so the engine binds to the test DB rather than a developer file.
_TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TEST_DB.close()
os.environ.setdefault("NOWGO_DATABASE_URL", f"sqlite+pysqlite:///{_TEST_DB.name}")
os.environ.setdefault("NOWGO_ADMIN_TOKEN", "test-admin-token")
os.environ.setdefault("NOWGO_PII_TOKEN_SECRET", "test-secret")


@pytest.fixture(scope="session")
def telemetry_event_schema() -> dict[str, Any]:
    """The canonical TelemetryEvent JSON Schema (draft 2020-12)."""
    path = SPECS_DIR / "telemetry-event.schema.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def ingestion_openapi_spec() -> dict[str, Any]:
    """The admin Ingestion API OpenAPI 3.1 spec."""
    path = SPECS_DIR / "ingestion-api.openapi.yaml"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture
def valid_telemetry_event() -> dict[str, Any]:
    """A minimally valid TelemetryEvent payload conforming to the schema."""
    return {
        "id": "01956f4d-3c5a-7c0a-8f0e-2d1d6e1f4a91",
        "source_slug": "ouvidor_sus_df",
        "external_id": "OSDF-2026-000123",
        "received_at": "2026-05-08T12:34:56Z",
        "occurred_at": "2026-05-08T12:30:00Z",
        "region_code": "5300108",
        "unit_code": "2645238",
        "topic": "acesso_consulta",
        "subtopic": "agendamento",
        "sentiment": -1,
        "severity": 2,
        "confidence": 0.82,
        "text_anonymized": "Cidadão relata atraso no agendamento de consulta na UBS.",
        "pii_tokens": ["pii:cpf:vault_2c1f", "pii:phone:vault_88b3"],
        "attributes": {"channel": "web", "language": "pt-BR"},
        "iso_37120": ["15.1", "15.2"],
        "iso_37122": ["SC-15.4"],
        "status": "classified",
    }


@pytest.fixture
def admin_auth_headers() -> dict[str, str]:
    """Bearer token accepted by the dev auth middleware."""
    return {"Authorization": "Bearer test-admin-token"}


@pytest.fixture
def client():
    """FastAPI TestClient with a freshly-initialised SQLite database."""
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from nowgo_saude import db
    from nowgo_saude.main import create_app

    db.Base.metadata.drop_all(bind=db.engine)
    db.init_db()
    app = create_app()
    with TestClient(app) as tc:
        yield tc
    with db.engine.begin() as conn:
        for table in ("audit_entries", "telemetry_events", "pipeline_runs", "sources"):
            conn.execute(text(f"DELETE FROM {table}"))


@pytest.fixture
def db_session():
    """Standalone session for unit tests touching the ORM directly."""
    from sqlalchemy import text

    from nowgo_saude import db

    db.Base.metadata.drop_all(bind=db.engine)
    db.init_db()
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()
        with db.engine.begin() as conn:
            for table in ("audit_entries", "telemetry_events", "pipeline_runs", "sources"):
                conn.execute(text(f"DELETE FROM {table}"))
