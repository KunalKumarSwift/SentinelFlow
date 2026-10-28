"""Contract every IdentityProvider implementation must satisfy."""

from collections.abc import Callable, Iterable

import pytest

from sentinelflow.contracts.identity import IdentityProvider
from sentinelflow.domain.actions import ActionKind, ProposedAction
from sentinelflow.domain.enrichment import UserContext
from sentinelflow.providers.identity.mock_identity import MockIdentity
from tests.fakes.fake_identity import FakeIdentityProvider

Factory = Callable[[Iterable[UserContext]], IdentityProvider]
IMPLEMENTATIONS: list[Factory] = [MockIdentity, FakeIdentityProvider]
ALICE = UserContext(user_id="alice", department="finance", is_privileged=True)


@pytest.fixture(params=IMPLEMENTATIONS, ids=lambda f: f.__name__)
def provider(request: pytest.FixtureRequest) -> IdentityProvider:
    factory: Factory = request.param
    return factory([ALICE])


def test_known_user_returns_context(provider: IdentityProvider) -> None:
    assert provider.lookup_user("alice") == ALICE


def test_unknown_user_returns_none(provider: IdentityProvider) -> None:
    assert provider.lookup_user("mallory") is None


DISABLE = ProposedAction(
    "inc-1:disable_user", "inc-1", ActionKind.DISABLE_USER, "alice", "r", "svc"
)


def test_apply_reports_success_for_known_target(provider: IdentityProvider) -> None:
    result = provider.apply(DISABLE, "run-1:call-1")
    assert (result.action_id, result.succeeded) == (DISABLE.id, True)


def test_apply_is_idempotent_per_key(provider: IdentityProvider) -> None:
    first = provider.apply(DISABLE, "run-1:call-1")
    assert provider.apply(DISABLE, "run-1:call-1") is first
