"""Static-token AuthProvider (dev/CI default).

Preserves the pre-T028 bearer-token contract: two long-lived tokens defined
in :class:`~nowgo_saude.config.Settings` map onto the ``admin`` and
``lgpd_officer`` roles respectively. The provider is **not** safe for
production — equality checks are not constant-time on Python ``str``, and
there is no expiration, rotation, or revocation. It exists so the OpenAPI
contract keeps working in CI without a live IdP.
"""

from __future__ import annotations

import hmac

from .provider import AuthError, AuthProvider, Principal

_BEARER_PREFIX = "Bearer "


class StaticTokenAuthProvider(AuthProvider):
    """Two-token equality-check provider.

    Constructor parameters mirror the relevant fields of ``Settings`` so
    callers can plug it in without importing the global settings module.

    Parameters
    ----------
    admin_token:
        Token whose presentation yields ``Principal(subject="admin",
        roles=("admin",))``.
    lgpd_officer_token:
        Token whose presentation yields a Principal with the
        ``lgpd_officer`` role and ``lgpd_authorized=True``.
    """

    def __init__(self, *, admin_token: str, lgpd_officer_token: str) -> None:
        self._admin_token = admin_token
        self._lgpd_officer_token = lgpd_officer_token

    def authenticate(self, authorization: str | None) -> Principal:
        if not authorization or not authorization.startswith(_BEARER_PREFIX):
            raise AuthError("missing or malformed bearer token")
        token = authorization[len(_BEARER_PREFIX):]

        # ``hmac.compare_digest`` is constant-time and resists timing attacks
        # even though the static backend is not production-grade — keeps the
        # downgrade path (JWT outage → static fallback) from leaking tokens.
        if hmac.compare_digest(token, self._admin_token):
            return Principal(subject="admin", roles=("admin",))
        if hmac.compare_digest(token, self._lgpd_officer_token):
            return Principal(
                subject="lgpd_officer",
                roles=("lgpd_officer",),
                lgpd_authorized=True,
            )
        raise AuthError("invalid bearer token")
