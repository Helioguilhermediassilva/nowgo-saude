"""Shared FastAPI dependencies (auth, sessions)."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import SessionLocal


def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(authorization: str | None = Header(default=None)) -> str:
    """Dev-grade bearer auth. Production swaps this for JWT verification."""
    settings = get_settings()
    expected = f"Bearer {settings.admin_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing bearer token"
        )
    return "admin"


AdminActor = Depends(require_admin)
DbSession = Depends(db_session)
