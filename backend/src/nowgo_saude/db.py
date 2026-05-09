"""SQLAlchemy engine, session factory and declarative base."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def normalize_db_url(url: str) -> str:
    """Coerce common managed-Postgres URLs into the psycopg 3 driver form.

    Providers like Railway/Supabase/Neon expose ``postgres://`` or
    ``postgresql://``; SQLAlchemy + psycopg 3 require the explicit
    ``postgresql+psycopg://`` scheme.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _engine_kwargs(url: str) -> dict[str, Any]:
    if url.startswith("sqlite"):
        # check_same_thread=False allows usage from FastAPI thread pool.
        return {"connect_args": {"check_same_thread": False}, "future": True}
    return {"future": True, "pool_pre_ping": True}


_settings = get_settings()
_db_url = normalize_db_url(_settings.database_url)
engine = create_engine(_db_url, **_engine_kwargs(_db_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables. Used by tests and the dev bootstrap."""
    # Import to register models on the metadata before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
