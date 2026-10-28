"""Per-tenant throttling by route group: allow under the limit, deny (429) above it."""

from datetime import timedelta

import pytest

from sentinelflow.domain.errors import RateLimitedError
from sentinelflow.providers.ratelimit.memory_rate_limiter import MemoryRateLimiter
from sentinelflow.security.throttle import DEFAULT_LIMITS, Throttle, route_group
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock


@pytest.mark.parametrize(
    ("method", "path", "group"),
    [
        ("POST", "/v1/alerts", "ingest"),
        ("GET", "/v1/incidents", "read"),
        ("GET", "/v1/alerts", "read"),
        ("POST", "/v1/approvals/apr-1/decision", "write"),
        ("POST", "/v1/workflows/triage/runs", "write"),
    ],
)
def test_route_group(method: str, path: str, group: str) -> None:
    assert route_group(method, path) == group


def _throttle() -> Throttle:
    return Throttle(MemoryRateLimiter(FakeClock(T0)), {"read": 2, "write": 2, "ingest": 2})


def test_requests_within_the_limit_pass() -> None:
    throttle = _throttle()
    throttle.check("acme", "GET", "/v1/incidents")
    throttle.check("acme", "GET", "/v1/incidents")


def test_request_over_the_limit_is_rejected_with_retry_after() -> None:
    throttle = _throttle()
    for _ in range(2):
        throttle.check("acme", "GET", "/v1/incidents")
    with pytest.raises(RateLimitedError, match="read") as caught:
        throttle.check("acme", "GET", "/v1/incidents")
    assert caught.value.retry_after == 1


def test_tenants_have_separate_budgets() -> None:
    throttle = _throttle()
    for _ in range(2):
        throttle.check("acme", "GET", "/v1/incidents")
    throttle.check("globex", "GET", "/v1/incidents")


def test_default_limits_follow_the_design() -> None:
    assert DEFAULT_LIMITS == {"ingest": 50, "read": 20, "write": 20}
    assert timedelta(seconds=1) == Throttle.WINDOW
