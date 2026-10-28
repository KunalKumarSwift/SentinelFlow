"""Contract for rate limiters: fixed windows per key (memory and Redis)."""

from collections.abc import Callable
from datetime import timedelta

import pytest

from sentinelflow.contracts.rate_limit import RateLimiter
from sentinelflow.providers.ratelimit.memory_rate_limiter import MemoryRateLimiter
from sentinelflow.providers.ratelimit.redis_rate_limiter import RedisRateLimiter
from tests.builders import T0
from tests.contracts.redis_backend import fresh_redis
from tests.fakes.fake_clock import FakeClock

WINDOW = timedelta(seconds=10)
Factory = Callable[[FakeClock], RateLimiter]
IMPLEMENTATIONS: list[Factory] = [
    MemoryRateLimiter,
    lambda clock: RedisRateLimiter(fresh_redis(), clock),
]


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(T0)


@pytest.fixture(params=IMPLEMENTATIONS)
def limiter(request: pytest.FixtureRequest, clock: FakeClock) -> RateLimiter:
    factory: Factory = request.param
    return factory(clock)


def test_hits_up_to_the_limit_are_allowed(limiter: RateLimiter) -> None:
    assert [limiter.hit("acme:read", 3, WINDOW) for _ in range(3)] == [None, None, None]


def test_hit_over_the_limit_reports_seconds_left(limiter: RateLimiter, clock: FakeClock) -> None:
    for _ in range(3):
        limiter.hit("acme:read", 3, WINDOW)
    clock.advance(timedelta(seconds=3, milliseconds=500))
    assert limiter.hit("acme:read", 3, WINDOW) == 7


def test_next_window_starts_fresh(limiter: RateLimiter, clock: FakeClock) -> None:
    for _ in range(4):
        limiter.hit("acme:read", 3, WINDOW)
    clock.advance(WINDOW)
    assert limiter.hit("acme:read", 3, WINDOW) is None


def test_keys_are_counted_separately(limiter: RateLimiter) -> None:
    limiter.hit("acme:read", 1, WINDOW)
    assert limiter.hit("globex:read", 1, WINDOW) is None
    assert limiter.hit("acme:write", 1, WINDOW) is None
    assert limiter.hit("acme:read", 1, WINDOW) is not None
