"""The facade picks process-local or Redis-backed queue and limiter from settings."""

from datetime import timedelta

from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.shared_state_facade import (
    make_rate_limiter,
    make_run_queue,
    make_token_budget,
)
from sentinelflow.providers.budget.memory_token_budget import MemoryTokenBudget
from sentinelflow.providers.budget.redis_token_budget import RedisTokenBudget
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.providers.queue.redis_queue import RedisRunQueue
from sentinelflow.providers.ratelimit.memory_rate_limiter import MemoryRateLimiter
from sentinelflow.providers.ratelimit.redis_rate_limiter import RedisRateLimiter
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock

TIMEOUT = timedelta(seconds=60)


def _settings(queue: str) -> Settings:
    return Settings(jwt_secret=SecretStr("s" * 32), queue_backend=queue)  # type: ignore[call-arg]


def test_memory_backend_is_process_local() -> None:
    settings, clock = _settings("memory"), FakeClock(T0)
    assert isinstance(make_run_queue(settings, clock, TIMEOUT), MemoryRunQueue)
    assert isinstance(make_rate_limiter(settings, clock), MemoryRateLimiter)
    assert isinstance(make_token_budget(settings, clock), MemoryTokenBudget)


def test_redis_backend_is_shared() -> None:
    # Clients connect lazily, so no Redis server is needed to build them.
    settings, clock = _settings("redis"), FakeClock(T0)
    assert isinstance(make_run_queue(settings, clock, TIMEOUT), RedisRunQueue)
    assert isinstance(make_rate_limiter(settings, clock), RedisRateLimiter)
    assert isinstance(make_token_budget(settings, clock), RedisTokenBudget)
