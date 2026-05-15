"""Shared FastAPI dependencies (auth, sessions).

Auth is delegated to :class:`~nowgo_saude.core.auth.AuthProvider` (T028); the
``require_*`` helpers translate :class:`AuthError` into ``HTTP 401`` and
missing roles into ``HTTP 403``. The returned string is the :attr:`Principal.subject`
so audit trails carry the real identity under the JWT backend while remaining
backward-compatible under the static backend (``"admin"`` / ``"lgpd_officer"``).
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..core.auth import AuthError, get_auth_provider
from ..db import SessionLocal


def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _authenticate(authorization: str | None, *, required_role: str) -> str:
    provider = get_auth_provider()
    try:
        principal = provider.authenticate(authorization)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    if not principal.has_role(required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"role '{required_role}' required",
        )
    return principal.subject


def require_admin(authorization: str | None = Header(default=None)) -> str:
    """Bearer auth requiring the ``admin`` role."""
    return _authenticate(authorization, required_role="admin")


def require_lgpd_officer(authorization: str | None = Header(default=None)) -> str:
    """Bearer auth requiring the ``lgpd_officer`` role for PII re-identification.

    The provider additionally enforces ``Principal.lgpd_authorized`` on the
    re-identify code-path; here we only gate by role so the dependency stays
    composable with non-LGPD audit endpoints that may share the role.
    """
    return _authenticate(authorization, required_role="lgpd_officer")


AdminActor = Depends(require_admin)
LgpdOfficer = Depends(require_lgpd_officer)
DbSession = Depends(db_session)
