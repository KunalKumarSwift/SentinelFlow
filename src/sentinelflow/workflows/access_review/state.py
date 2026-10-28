"""State of one access-review run (not checkpointed: the run is short and idempotent)."""

from typing import Protocol, TypedDict

from sentinelflow.domain.access_review import Account, Finding
from sentinelflow.domain.incidents import Incident


class ReviewState(TypedDict, total=False):
    """Tenant under review and what each node produced."""

    tenant_id: str
    accounts: tuple[Account, ...]
    findings: tuple[Finding, ...]
    new_incidents: tuple[Incident, ...]


class TenantInput(TypedDict):
    """What ``list_accounts`` reads."""

    tenant_id: str


class AccountsInput(TypedDict):
    """What ``review`` reads."""

    accounts: tuple[Account, ...]


class FindingsInput(TypedDict):
    """What ``raise_findings`` reads."""

    tenant_id: str
    findings: tuple[Finding, ...]


class Node[In](Protocol):
    """An access-review node: reads its declared input, returns a partial update."""

    def __call__(self, state: In) -> ReviewState:
        """Run the node."""
        ...
