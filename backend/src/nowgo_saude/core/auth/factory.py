"""Factory that wires the configured :class:`AuthProvider` from Settings.

Cached per-process so endpoints reuse a single instance. ``get_auth_provider``
is intentionally a thin function (not a class) so it can be overridden in
tests via ``app.dependency_overrides`` if needed.
"""

from __future__ import annotations

from functools import lru_cache

from ...config import get_settings
from .jwt_provider import JwtAuthProvider
from .provider import AuthProvider
from .static_provider import StaticTokenAuthProvider


@lru_cache(maxsize=1)
def get_auth_provider() -> AuthProvider:
    """Build (and cache) the :class:`AuthProvider` selected by Settings.

    Selection rules:
    * ``NOWGO_AUTH_BACKEND=static`` (default) → :class:`StaticTokenAuthProvider`
    * ``NOWGO_AUTH_BACKEND=jwt`` → :class:`JwtAuthProvider`

    Unknown values fall back to ``static`` to preserve the contract in misconfigured
    environments — the deployment pipeline should reject unknown values upstream.
    """
    settings = get_settings()
    if settings.auth_backend == "jwt":
        return JwtAuthProvider(
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    return StaticTokenAuthProvider(
        admin_token=settings.admin_token,
        lgpd_officer_token=settings.lgpd_officer_token,
    )


def reset_auth_provider_cache() -> None:
    """Drop the cached provider. Test-only hook; production never calls this."""
    get_auth_provider.cache_clear()
