"""Build a ``RedisRunQueue`` from a URL (kept apart so the queue takes a ready client)."""

from datetime import timedelta

from redis import Redis

from sentinelflow.core.clock import Clock
from sentinelflow.providers.queue.redis_queue import RedisRunQueue


def open_redis_queue(url: str, clock: Clock, timeout: timedelta) -> RedisRunQueue:
    """Return a queue on ``url``; responses are decoded to ``str`` as the queue expects."""
    client = Redis.from_url(url, decode_responses=True)  # pyright: ignore[reportUnknownMemberType] -- untyped **kwargs
    return RedisRunQueue(client, clock, timeout)
