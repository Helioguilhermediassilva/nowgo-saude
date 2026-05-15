"""JWT AuthProvider (production-ready, MVP scope).

Validates a Bearer JWT using ``python-jose``: signature against the configured
secret (HS*) or public key (RS*), plus the standard temporal/issuer/audience
checks. ``roles`` is read from a custom claim (string list); ``lgpd_authorized``
is read from a boolean claim of the same name.

What this provider deliberately does **not** do (deferred to T041 or a
follow-up spec):

* JWKS rotation — the secret/key is loaded once from Settings.
* Token revocation lists — JWTs are stateless by construction.
* Refresh-token issuance — the IdP owns the login flow.
"""

from __future__ import annotations

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from .provider import AuthError, AuthProvider, Principal

_BEARER_PREFIX = "Bearer "
_ROLES_CLAIM = "roles"
_LGPD_CLAIM = "lgpd_authorized"


class JwtAuthProvider(AuthProvider):
    """JWT validator wired to the standard claims (``sub``, ``exp``, ``iss``,
    ``aud``) plus the project-specific ``roles`` and ``lgpd_authorized``.

    Parameters
    ----------
    secret:
        Shared secret (HS*) or PEM-encoded public key (RS*). The choice of
        algorithm in ``algorithm`` determines how it is consumed by
        ``jose.jwt.decode``.
    algorithm:
        Allowed algorithm. We intentionally accept only ONE algorithm at a
        time to prevent the classic "alg=none" / algorithm-confusion attack.
    issuer:
        Expected ``iss`` claim. Tokens with a different issuer are rejected.
    audience:
        Expected ``aud`` claim. Multi-audience tokens MUST include this value.
    """

    def __init__(
        self,
        *,
        secret: str,
        algorithm: str,
        issuer: str,
        audience: str,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience

    def authenticate(self, authorization: str | None) -> Principal:
        if not authorization or not authorization.startswith(_BEARER_PREFIX):
            raise AuthError("missing or malformed bearer token")
        token = authorization[len(_BEARER_PREFIX):]

        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
            )
        except ExpiredSignatureError as exc:
            raise AuthError("token expired") from exc
        except JWTError as exc:
            # ``JWTError`` covers bad signature, wrong iss/aud, malformed
            # payload, etc. We surface a generic message to avoid telling an
            # attacker which check failed.
            raise AuthError(f"invalid token: {exc}") from exc

        subject = claims.get("sub")
        if not subject or not isinstance(subject, str):
            raise AuthError("token missing 'sub' claim")

        raw_roles = claims.get(_ROLES_CLAIM, [])
        if not isinstance(raw_roles, list) or not all(
            isinstance(r, str) for r in raw_roles
        ):
            raise AuthError(f"token '{_ROLES_CLAIM}' claim must be a list of strings")

        return Principal(
            subject=subject,
            roles=tuple(raw_roles),
            lgpd_authorized=bool(claims.get(_LGPD_CLAIM, False)),
        )
