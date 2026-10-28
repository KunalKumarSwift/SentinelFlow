"""Contract for token budgets: per tenant, per UTC day, never overspent (memory and Redis)."""

from collections.abc import Callable
from datetime import timedelta

import pytest

from sentinelflow.contracts.token_budget import TokenBudget
from sentinelflow.providers.budget.memory_token_budget import MemoryTokenBudget
from sentinelflow.providers.budget.redis_token_budget import RedisTokenBudget
from tests.builders import T0
from tests.contracts.redis_backend import fresh_redis
from tests.fakes.fake_clock import FakeClock

Factory = Callable[[FakeClock], TokenBudget]
IMPLEMENTATIONS: list[Factory] = [
    MemoryTokenBudget,
    lambda clock: RedisTokenBudget(fresh_redis(), clock),
]


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(T0)


@pytest.fixture(params=IMPLEMENTATIONS)
def budget(request: pytest.FixtureRequest, clock: FakeClock) -> TokenBudget:
    factory: Factory = request.param
    return factory(clock)


def test_spending_within_the_limit_is_allowed(budget: TokenBudget) -> None:
    assert budget.try_spend("acme", 600, 1000) and budget.try_spend("acme", 400, 1000)


def test_refused_spend_reserves_nothing(budget: TokenBudget) -> None:
    budget.try_spend("acme", 900, 1000)
    assert not budget.try_spend("acme", 200, 1000)
    assert budget.try_spend("acme", 100, 1000)


def test_tenants_have_separate_budgets(budget: TokenBudget) -> None:
    budget.try_spend("acme", 1000, 1000)
    assert budget.try_spend("globex", 1000, 1000)


def test_a_new_day_starts_fresh(budget: TokenBudget, clock: FakeClock) -> None:
    budget.try_spend("acme", 1000, 1000)
    clock.advance(timedelta(days=1))
    assert budget.try_spend("acme", 1000, 1000)
