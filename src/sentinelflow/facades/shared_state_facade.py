"""Choose the run queue, rate limiter and token budget from settings. Switch logic only.

With ``QUEUE_BACKEND=redis`` both live in Redis, so every API replica and worker
shares them; otherwise they are process-local.
"""

from datetime import timedelta

from sentinelflow.contracts.rate_limit import RateLimiter
from sentinelflow.contracts.run_queue import RunQueue
from sentinelflow.contracts.token_budget import TokenBudget
from sentinelflow.core.clock import Clock
from sentinelflow.core.config import Settings


def make_run_queue(settings: Settings, clock: Clock, timeout: timedelta) -> RunQueue:
    """Return the configured run queue (``timeout`` = visibility timeout)."""
    if settings.queue_backend == "redis":
        from sentinelflow.providers.queue.redis_queue import RedisRunQueue
        from sentinelflow.providers.redis_client import open_redis

        return RedisRunQueue(open_redis(settings.redis_url), clock, timeout)
    from sentinelflow.providers.queue.memory_queue import MemoryRunQueue

    return MemoryRunQueue(clock, timeout)


def make_rate_limiter(settings: Settings, clock: Clock) -> RateLimiter:
    """Return the configured rate limiter."""
    if settings.queue_backend == "redis":
        from sentinelflow.providers.ratelimit.redis_rate_limiter import RedisRateLimiter
        from sentinelflow.providers.redis_client import open_redis

        return RedisRateLimiter(open_redis(settings.redis_url), clock)
    from sentinelflow.providers.ratelimit.memory_rate_limiter import MemoryRateLimiter

    return MemoryRateLimiter(clock)


def make_token_budget(settings: Settings, clock: Clock) -> TokenBudget:
    """Return the configured daily LLM token budget store."""
    if settings.queue_backend == "redis":
        from sentinelflow.providers.budget.redis_token_budget import RedisTokenBudget
        from sentinelflow.providers.redis_client import open_redis

        return RedisTokenBudget(open_redis(settings.redis_url), clock)
    from sentinelflow.providers.budget.memory_token_budget import MemoryTokenBudget

    return MemoryTokenBudget(clock)
