"""Read a tenant's whole audit chain page by page."""

from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.domain.audit import AuditEvent

PAGE = 500


def read_all(store: AuditStore, tenant_id: str) -> list[AuditEvent]:
    """Return every event of the tenant's chain in order."""
    events: list[AuditEvent] = []
    while page := store.read(tenant_id, events[-1].seq if events else 0, PAGE):
        events.extend(page)
    return events
