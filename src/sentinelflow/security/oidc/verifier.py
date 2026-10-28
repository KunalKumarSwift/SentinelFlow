"""Verify Keycloak (OIDC) access tokens: RS256 only, realm JWKS, issuer, audience, expiry."""

from collections.abc import Mapping
from datetime import timedelta

from sentinelflow.core.clock import Clock
from sentinelflow.domain.errors import AuthenticationError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.oidc import _rs256
from sentinelflow.security.oidc.claims import principal_from_keycloak
from sentinelflow.security.oidc.jwks import CachedJwks

MAX_LIFETIME = timedelta(hours=1)
_REQUIRED = ["sub", "iss", "aud", "iat", "exp"]


class OidcTokenVerifier:
    """``TokenVerifier`` for bearer tokens issued by the identity provider."""

    def __init__(self, keys: CachedJwks, issuer: str, audience: str, clock: Clock) -> None:
        """Trust tokens from ``issuer`` meant for ``audience``, signed by a key in ``keys``."""
        self._keys, self._issuer, self._audience, self._clock = keys, issuer, audience, clock

    def verify(self, token: str) -> Principal:
        """Return the principal a valid token represents.

        Raises:
            AuthenticationError: If the token is malformed, forged, expired or not for us.
        """
        claims = self._decode(token)
        self._check_lifetime(claims)
        return principal_from_keycloak(claims)

    def _decode(self, token: str) -> Mapping[str, object]:
        try:
            kid = _rs256.key_id(token)
            key = None if kid is None else self._keys.key(kid)
            if key is None:
                raise AuthenticationError("token signed by an unknown signing key")
            return _rs256.decode(token, key, self._issuer, self._audience, _REQUIRED)
        except _rs256.InvalidIssuerError as exc:
            raise AuthenticationError("invalid token issuer") from exc
        except _rs256.InvalidAudienceError as exc:
            raise AuthenticationError("invalid token audience") from exc
        except _rs256.InvalidTokenError as exc:
            raise AuthenticationError(f"invalid token: {type(exc).__name__}") from exc

    def _check_lifetime(self, claims: Mapping[str, object]) -> None:
        issued, expires = claims["iat"], claims["exp"]
        if not isinstance(issued, int) or not isinstance(expires, int):
            raise AuthenticationError("claims 'iat' and 'exp' must be integers")
        if expires - issued > MAX_LIFETIME.total_seconds():
            raise AuthenticationError(f"token lifetime exceeds {MAX_LIFETIME}")
        if self._clock.now().timestamp() >= expires:
            raise AuthenticationError("token expired")
