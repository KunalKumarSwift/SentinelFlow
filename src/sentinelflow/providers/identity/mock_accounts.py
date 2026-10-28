"""Account directory served from in-memory data (demo seed or tests)."""

from collections.abc import Iterable, Sequence

from sentinelflow.domain.access_review import Account


class MockAccountDirectory:
    """``AccountDirectory`` over a fixed list of accounts."""

    def __init__(self, accounts: Iterable[Account]) -> None:
        """Serve ``accounts``."""
        self._accounts = tuple(accounts)

    def list_accounts(self, tenant_id: str) -> Sequence[Account]:
        """Return the tenant's accounts in their original order."""
        return [a for a in self._accounts if a.tenant_id == tenant_id]
