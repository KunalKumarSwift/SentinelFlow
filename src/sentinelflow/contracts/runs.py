"""Storage interface for workflow run records."""

from typing import Protocol

from sentinelflow.domain.runs import RunRecord


class RunRepository(Protocol):
    """Tenant-scoped run-record store."""

    def add(self, record: RunRecord) -> None:
        """Persist a new run record."""
        ...

    def get(self, tenant_id: str, run_id: str) -> RunRecord | None:
        """Return the record, or ``None`` if absent or owned by another tenant."""
        ...

    def update(self, record: RunRecord) -> None:
        """Replace a stored record. Raises ``KeyError`` if it does not exist."""
        ...
