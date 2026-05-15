"""Auth plug-point (T028).

The :class:`AuthProvider` ABC isolates token validation from FastAPI deps so
the production adapter (JWT) can be swapped in via configuration without any
endpoint changes. The MVP ships two adapters:

* :class:`StaticTokenAuthProvider` — equality check against tokens defined in
  :class:`~nowgo_saude.config.Settings`. Default for dev/CI; preserves the
  bearer-token contract that the OpenAPI spec advertised before T028.
* :class:`JwtAuthProvider` — full HS256/RS256 JWT validation (signature,
  ``exp``, ``nbf``, ``iss``, ``aud``) reading roles from a ``roles`` claim.

T041 will layer middleware on top of this interface (rate limiting, structured
audit of failed attempts). T028 only lands the contract + the two adapters.
"""

from .factory import get_auth_provider
from .jwt_provider import JwtAuthProvider
from .provider import AuthError, AuthProvider, Principal
from .static_provider import StaticTokenAuthProvider

__all__ = [
    "AuthError",
    "AuthProvider",
    "JwtAuthProvider",
    "Principal",
    "StaticTokenAuthProvider",
    "get_auth_provider",
]
