"""Per-tenant rate limiting: 429 problem with Retry-After above the limit."""

from fastapi.testclient import TestClient

from sentinelflow.api.app import create_app
from sentinelflow.providers.ratelimit.memory_rate_limiter import MemoryRateLimiter
from sentinelflow.security.throttle import Throttle
from sentinelflow.security.tokens import Hs256TokenService
from tests.api.conftest import TokenFor, make_container
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock


def _client(tokens: Hs256TokenService) -> TestClient:
    throttle = Throttle(MemoryRateLimiter(FakeClock(T0)), {"read": 2, "write": 2, "ingest": 2})
    return TestClient(create_app(make_container(tokens, throttle=throttle)))


def test_requests_under_the_limit_succeed(tokens: Hs256TokenService, auth: TokenFor) -> None:
    client = _client(tokens)
    headers = auth("soc-analyst-l1")
    assert [client.get("/v1/incidents", headers=headers).status_code for _ in range(2)] == [
        200,
        200,
    ]


def test_request_over_the_limit_is_429_with_retry_after(
    tokens: Hs256TokenService, auth: TokenFor
) -> None:
    client = _client(tokens)
    headers = auth("soc-analyst-l1")
    for _ in range(2):
        client.get("/v1/incidents", headers=headers)
    response = client.get("/v1/incidents", headers=headers)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    assert response.json()["title"] == "Too Many Requests"


def test_other_tenants_are_not_affected(tokens: Hs256TokenService, auth: TokenFor) -> None:
    client = _client(tokens)
    for _ in range(3):
        client.get("/v1/incidents", headers=auth("soc-analyst-l1"))
    other = client.get("/v1/incidents", headers=auth("soc-analyst-l1", tenant="globex"))
    assert other.status_code == 200
