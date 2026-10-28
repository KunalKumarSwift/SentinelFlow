"""Fixed-window rate limiter on Redis, shared by every API replica.

Key ``sf:ratelimit:{key}:{window}`` is incremented atomically and expires two windows
later, so Redis holds only current counters.
"""

from datetime import timedelta

from redis import Redis

from sentinelflow.core.clock import Clock
from sentinelflow.providers.ratelimit.window import seconds_left, window_index


class RedisRateLimiter:
    """``RateLimiter`` backed by ``INCR`` + ``PEXPIRE`` in one transaction."""

    def __init__(self, client: Redis, clock: Clock, prefix: str = "sf:ratelimit") -> None:
        """Use ``client`` and measure windows with ``clock``."""
        self._r, self._clock, self._prefix = client, clock, prefix

    def hit(self, key: str, limit: int, window: timedelta) -> int | None:
        """Count a hit; return seconds to wait if ``limit`` is exceeded."""
        now = self._clock.now()
        counter = f"{self._prefix}:{key}:{window_index(now, window)}"
        with self._r.pipeline() as tx:  # pyright: ignore[reportUnknownMemberType] -- untyped shard_hint
            tx.incr(counter)
            tx.pexpire(counter, window * 2)
            hits, _ = tx.execute()
        return None if int(hits) <= limit else seconds_left(now, window)
