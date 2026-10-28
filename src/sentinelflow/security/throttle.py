"""Per-tenant API throttling by route group (LLD 07 §5).

Limits are per tenant, so one noisy tenant cannot starve the others; the counter is
shared through the injected ``RateLimiter`` when the API runs as several replicas.
"""

from collections.abc import Mapping
from datetime import timedelta
from types import MappingProxyType

from sentinelflow.contracts.rate_limit import RateLimiter
from sentinelflow.domain.errors import RateLimitedError

# Requests per second per tenant. Ingest is higher: detection sources burst.
DEFAULT_LIMITS: Mapping[str, int] = MappingProxyType({"ingest": 50, "read": 20, "write": 20})


def route_group(method: str, path: str) -> str:
    """Return ``ingest`` for alert ingestion, ``read`` for GETs and ``write`` otherwise."""
    if method == "POST" and path.rstrip("/") == "/v1/alerts":
        return "ingest"
    return "read" if method == "GET" else "write"


class Throttle:
    """Applies ``limits`` per tenant and route group."""

    WINDOW = timedelta(seconds=1)

    def __init__(self, limiter: RateLimiter, limits: Mapping[str, int] = DEFAULT_LIMITS) -> None:
        """Count with ``limiter``; ``limits`` maps route group to requests per second."""
        self._limiter, self._limits = limiter, limits

    def check(self, tenant_id: str, method: str, path: str) -> None:
        """Admit the request or raise.

        Raises:
            RateLimitedError: If the tenant exceeded the group's limit this second.
        """
        group = route_group(method, path)
        wait = self._limiter.hit(f"{tenant_id}:{group}", self._limits[group], self.WINDOW)
        if wait is not None:
            raise RateLimitedError(f"rate limit exceeded for {group} requests", retry_after=wait)
