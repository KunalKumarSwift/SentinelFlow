"""Issue and verify short-lived HS256 access tokens (Phases 1-3; Keycloak RS256 later).

Only HS256 is accepted, so ``alg: none`` and algorithm-confusion tokens are rejected.
Expiry is checked against the injected ``Clock`` instead of PyJWT's wall clock, which
keeps the check deterministic in tests; PyJWT still verifies signature and issuer.
"""

from collections.abc import Mapping
from datetime import timedelta

from sentinelflow.core.clock import Clock
from sentinelflow.domain.errors import AuthenticationError
from sentinelflow.domain.principals import Principal
from sentinelflow.security import _jwt
from sentinelflow.security._claims import claims_for, principal_from

ISSUER = "sentinelflow"
MAX_LIFETIME = timedelta(minutes=15)
_REQUIRED = ["sub", "iss", "iat", "exp"]


class Hs256TokenService:
    """Creates and checks bearer tokens signed with a shared secret."""

    def __init__(self, secret: str, clock: Clock, ttl: timedelta = MAX_LIFETIME) -> None:
        """Configure the service.

        Raises:
            ValueError: If the secret is shorter than 32 characters or ``ttl`` is too long.
        """
        if len(secret) < 32:
            raise ValueError("token secret must be at least 32 characters")
        if ttl > MAX_LIFETIME:
            raise ValueError(f"token ttl must not exceed {MAX_LIFETIME}")
        self._secret, self._clock, self._ttl = secret, clock, ttl

    def issue(self, principal: Principal) -> str:
        """Return a signed token for ``principal`` valid for the configured ttl."""
        now = self._clock.now()
        claims = claims_for(principal, now, now + self._ttl, ISSUER)
        return _jwt.encode(claims, self._secret)

    def verify(self, token: str) -> Principal:
        """Return the principal a valid token represents.

        Raises:
            AuthenticationError: If the token is malformed, forged, expired or too long-lived.
        """
        claims = self._decode(token)
        self._check_lifetime(claims)
        return principal_from(claims)

    def _decode(self, token: str) -> Mapping[str, object]:
        try:
            return _jwt.decode(token, self._secret, ISSUER, _REQUIRED)
        except _jwt.InvalidSignatureError as exc:
            raise AuthenticationError("invalid token signature") from exc
        except _jwt.InvalidIssuerError as exc:
            raise AuthenticationError("invalid token issuer") from exc
        except _jwt.InvalidTokenError as exc:
            raise AuthenticationError(f"invalid token: {exc}") from exc

    def _check_lifetime(self, claims: Mapping[str, object]) -> None:
        issued, expires = claims["iat"], claims["exp"]
        if not isinstance(issued, int) or not isinstance(expires, int):
            raise AuthenticationError("claims 'iat' and 'exp' must be integers")
        if expires - issued > MAX_LIFETIME.total_seconds():
            raise AuthenticationError(f"token lifetime exceeds {MAX_LIFETIME}")
        if self._clock.now().timestamp() >= expires:
            raise AuthenticationError("token expired")
