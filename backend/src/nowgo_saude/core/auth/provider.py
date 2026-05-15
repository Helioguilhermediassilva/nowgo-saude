"""AuthProvider abstract base + Principal value object (T028).

The ``authenticate`` contract is intentionally narrow: it takes the raw
``Authorization`` header value (or ``None``) and returns a fully-populated
``Principal``. Validation failures raise :class:`AuthError`; the FastAPI deps
layer translates that into an HTTP 401 so providers stay framework-agnostic
and unit-testable in isolation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated identity carried through the request lifecycle.

    Attributes
    ----------
    subject:
        Stable identifier for the caller. For JWT this is the ``sub`` claim
        (typically an opaque user id from the IdP); for the static backend it
        is the role name (``"admin"`` / ``"lgpd_officer"``) so the audit trail
        remains populated even in dev/CI.
    roles:
        Authoritative role tuple used by :meth:`has_role`. We use a tuple so
        ``Principal`` stays hashable and safely shareable across threads.
    lgpd_authorized:
        Hard switch for PII re-identification. The static backend sets this
        to ``True`` only for the LGPD-officer token; the JWT backend reads
        the optional ``lgpd_authorized`` boolean claim. We keep it separate
        from ``roles`` so RBAC and LGPD authorisation can evolve independently.
    """

    subject: str
    roles: tuple[str, ...] = field(default_factory=tuple)
    lgpd_authorized: bool = False

    def has_role(self, role: str) -> bool:
        return role in self.roles


class AuthError(Exception):
    """Raised by an :class:`AuthProvider` when authentication fails.

    The ``detail`` is safe to surface in an HTTP 401 body (it never carries
    secrets or PII). Providers MUST classify both *missing* and *invalid*
    credentials as :class:`AuthError`; the deps layer translates uniformly to
    ``401`` to avoid leaking whether a token is well-formed.
    """


class AuthProvider(ABC):
    """Strategy interface for validating an ``Authorization`` header.

    Implementations MUST be stateless (or carry only immutable configuration)
    so a single instance can serve concurrent requests. The :func:`factory`
    module caches one instance per process.
    """

    @abstractmethod
    def authenticate(self, authorization: str | None) -> Principal:
        """Parse and validate ``authorization``; return the :class:`Principal`.

        Parameters
        ----------
        authorization:
            Raw header value (``"Bearer <token>"``) or ``None`` when the
            header was omitted. Implementations MUST raise :class:`AuthError`
            for any anomaly — never return an "anonymous" Principal — so the
            deps layer can default to 401 without explicit None-checks.
        """
        raise NotImplementedError
