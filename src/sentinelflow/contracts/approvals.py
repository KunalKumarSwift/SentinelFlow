"""Storage interface for approvals."""

from collections.abc import Sequence
from typing import Protocol

from sentinelflow.domain.approvals import Approval


class ApprovalRepository(Protocol):
    """Tenant-scoped approval store."""

    def add(self, approval: Approval) -> None:
        """Persist a new approval. Raises ``ValueError`` if the id exists."""
        ...

    def get(self, tenant_id: str, approval_id: str) -> Approval | None:
        """Return the approval, or ``None`` if absent or owned by another tenant."""
        ...

    def update(self, approval: Approval) -> None:
        """Replace a stored approval. Raises ``KeyError`` if it does not exist."""
        ...

    def for_run(self, tenant_id: str, run_id: str) -> Sequence[Approval]:
        """Return the run's approvals in creation order."""
        ...

    def pending(self, tenant_id: str) -> Sequence[Approval]:
        """Return the tenant's pending approvals in creation order."""
        ...
