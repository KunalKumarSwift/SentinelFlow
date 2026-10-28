"""Contract for account directories: tenant-scoped listing."""

from collections.abc import Callable

import pytest

from sentinelflow.contracts.accounts import AccountDirectory
from sentinelflow.domain.access_review import Account
from sentinelflow.providers.identity.mock_accounts import MockAccountDirectory
from tests.builders import T0

ACCOUNTS = (
    Account("alice", "acme", frozenset({"soc-analyst-l1"}), T0, None),
    Account("gus", "globex", frozenset({"auditor"}), T0, None),
)
IMPLEMENTATIONS: list[Callable[[], AccountDirectory]] = [lambda: MockAccountDirectory(ACCOUNTS)]


@pytest.fixture(params=IMPLEMENTATIONS)
def directory(request: pytest.FixtureRequest) -> AccountDirectory:
    return request.param()


def test_lists_only_the_tenants_accounts(directory: AccountDirectory) -> None:
    assert [a.user_id for a in directory.list_accounts("acme")] == ["alice"]
    assert directory.list_accounts("initech") == []
