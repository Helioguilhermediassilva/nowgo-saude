"""Unit tests for the database URL normalizer (managed-Postgres compatibility)."""

from __future__ import annotations

import pytest

from nowgo_saude.db import normalize_db_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgres://u:p@host:5432/db",
            "postgresql+psycopg://u:p@host:5432/db",
        ),
        (
            "postgresql://u:p@host:5432/db",
            "postgresql+psycopg://u:p@host:5432/db",
        ),
        (
            "postgresql+psycopg://u:p@host:5432/db",
            "postgresql+psycopg://u:p@host:5432/db",
        ),
        (
            "sqlite+pysqlite:///./nowgo_saude.db",
            "sqlite+pysqlite:///./nowgo_saude.db",
        ),
    ],
)
def test_normalize_db_url(raw: str, expected: str) -> None:
    assert normalize_db_url(raw) == expected
