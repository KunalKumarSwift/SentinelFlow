"""Daily token budget in Redis, shared by every worker.

Key ``sf:budget:{tenant}:{yyyymmdd}`` expires after 48 h. ``INCRBY`` reserves first; a
reservation that overshoots is rolled back with ``DECRBY``, so concurrent workers can
never spend past the limit together.
"""

from datetime import timedelta

from redis import Redis

from sentinelflow.core.clock import Clock

_TTL = timedelta(hours=48)


class RedisTokenBudget:
    """``TokenBudget`` backed by atomic Redis counters."""

    def __init__(self, client: Redis, clock: Clock, prefix: str = "sf:budget") -> None:
        """Use ``client`` and decide "today" (UTC) with ``clock``."""
        self._r, self._clock, self._prefix = client, clock, prefix

    def try_spend(self, tenant_id: str, tokens: int, daily_limit: int) -> bool:
        """Reserve ``tokens`` if the tenant stays within ``daily_limit`` today."""
        key = f"{self._prefix}:{tenant_id}:{self._clock.now():%Y%m%d}"
        with self._r.pipeline() as tx:  # pyright: ignore[reportUnknownMemberType] -- untyped shard_hint
            tx.incrby(key, tokens)
            tx.pexpire(key, _TTL)
            total, _ = tx.execute()
        if int(total) > daily_limit:
            self._r.decrby(key, tokens)
            return False
        return True
