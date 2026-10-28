"""In-memory run-record store for tests and single-process mode."""

from sentinelflow.domain.runs import RunRecord


class MemoryRunRepository:
    """Keeps run records in a dict keyed by tenant and id."""

    def __init__(self) -> None:
        """Start empty."""
        self._items: dict[tuple[str, str], RunRecord] = {}

    def add(self, record: RunRecord) -> None:
        """Store a new record (``ValueError`` if it exists)."""
        key = (record.tenant_id, record.id)
        if key in self._items:
            raise ValueError(f"run {record.id} already exists")
        self._items[key] = record

    def get(self, tenant_id: str, run_id: str) -> RunRecord | None:
        """Return the tenant's record, if any."""
        return self._items.get((tenant_id, run_id))

    def update(self, record: RunRecord) -> None:
        """Replace a stored record (``KeyError`` if missing)."""
        key = (record.tenant_id, record.id)
        if key not in self._items:
            raise KeyError(f"run {record.id} does not exist")
        self._items[key] = record
