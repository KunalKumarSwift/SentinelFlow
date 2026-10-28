"""Cached JSON Web Key Set of the identity provider.

Keys are refreshed after ``ttl`` and when a token names an unknown ``kid`` (the IdP
rotated its key), but at most once per ``MIN_REFRESH``, so a flood of tokens with
made-up key ids cannot turn into a flood of requests to the IdP.
"""

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from threading import Lock

import jwt

from sentinelflow.core.clock import Clock
from sentinelflow.security.oidc._rs256 import parse_jwks

MIN_REFRESH = timedelta(seconds=30)
Fetch = Callable[[], Mapping[str, object]]


class CachedJwks:
    """Looks up verification keys by ``kid``; ``fetch`` downloads the JWKS document."""

    def __init__(self, fetch: Fetch, clock: Clock, ttl: timedelta = timedelta(hours=1)) -> None:
        """Fetch lazily on first use."""
        self._fetch, self._clock, self._ttl = fetch, clock, ttl
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at: datetime | None = None
        self._lock = Lock()

    def key(self, kid: str) -> jwt.PyJWK | None:
        """Return the key for ``kid``, refreshing the set when allowed."""
        with self._lock:
            if self._stale() or (kid not in self._keys and self._may_refresh()):
                self._keys = parse_jwks(self._fetch())
                self._fetched_at = self._clock.now()
            return self._keys.get(kid)

    def _stale(self) -> bool:
        return self._fetched_at is None or self._clock.now() - self._fetched_at >= self._ttl

    def _may_refresh(self) -> bool:
        assert self._fetched_at is not None  # noqa: S101 -- _stale() handled the first fetch
        return self._clock.now() - self._fetched_at >= MIN_REFRESH
