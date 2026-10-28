"""Interface to the directory's account list (used by the access review)."""

from collections.abc import Sequence
from typing import Protocol

from sentinelflow.domain.access_review import Account


class AccountDirectory(Protocol):
    """Lists accounts with their roles and activity."""

    def list_accounts(self, tenant_id: str) -> Sequence[Account]:
        """Return every account of ``tenant_id`` (none for an unknown tenant).

        Raises:
            ProviderError: If the directory cannot be reached (real providers only).
        """
        ...
