"""In-memory approval store for tests and single-process mode."""

from collections.abc import Sequence

from sentinelflow.domain.approvals import Approval, ApprovalStatus


class MemoryApprovalRepository:
    """Keeps approvals in an insertion-ordered dict keyed by tenant and id."""

    def __init__(self) -> None:
        """Start empty."""
        self._items: dict[tuple[str, str], Approval] = {}

    def add(self, approval: Approval) -> None:
        """Store a new approval (``ValueError`` if it exists)."""
        key = (approval.tenant_id, approval.id)
        if key in self._items:
            raise ValueError(f"approval {approval.id} already exists")
        self._items[key] = approval

    def get(self, tenant_id: str, approval_id: str) -> Approval | None:
        """Return the tenant's approval, if any."""
        return self._items.get((tenant_id, approval_id))

    def update(self, approval: Approval) -> None:
        """Replace a stored approval (``KeyError`` if missing)."""
        key = (approval.tenant_id, approval.id)
        if key not in self._items:
            raise KeyError(f"approval {approval.id} does not exist")
        self._items[key] = approval

    def for_run(self, tenant_id: str, run_id: str) -> Sequence[Approval]:
        """Return the run's approvals."""
        return [a for (t, _), a in self._items.items() if t == tenant_id and a.run_id == run_id]

    def pending(self, tenant_id: str) -> Sequence[Approval]:
        """Return the tenant's pending approvals."""
        own = (a for (t, _), a in self._items.items() if t == tenant_id)
        return [a for a in own if a.status is ApprovalStatus.PENDING]
