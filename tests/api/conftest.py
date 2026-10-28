"""API test wiring: an app built from fakes and helpers to mint tokens."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from sentinelflow.api.app import create_app
from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.security.tokens import Hs256TokenService
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock

SECRET = "a" * 32
TokenFor = Callable[..., dict[str, str]]


@pytest.fixture
def tokens() -> Hs256TokenService:
    return Hs256TokenService(secret=SECRET, clock=FakeClock(T0))


def make_container(tokens: Hs256TokenService, app_env: str = "dev") -> ApiContainer:
    """Return a container wired with test doubles."""
    return ApiContainer(app_env=app_env, tokens=tokens)


@pytest.fixture
def client(tokens: Hs256TokenService) -> TestClient:
    return TestClient(create_app(make_container(tokens)))


@pytest.fixture
def auth(tokens: Hs256TokenService) -> TokenFor:
    """Return Authorization headers for a principal with the given roles."""

    def headers(*roles: str, tenant: str = "acme", kind: str = "user") -> dict[str, str]:
        principal = Principal("u-1", tenant, "soc-emea", frozenset(roles), PrincipalKind(kind))
        return {"Authorization": f"Bearer {tokens.issue(principal)}"}

    return headers
