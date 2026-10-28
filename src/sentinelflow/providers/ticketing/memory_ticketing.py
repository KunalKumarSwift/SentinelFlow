"""In-memory ticketing for tests and single-process mode."""

from sentinelflow.contracts.ticketing import Ticket


class MemoryTicketing:
    """Keeps tickets in a dict keyed by tenant and incident."""

    def __init__(self) -> None:
        """Start empty."""
        self._tickets: dict[tuple[str, str], Ticket] = {}

    def upsert(self, tenant_id: str, incident_id: str, title: str, body: str) -> str:
        """Create or replace the incident's ticket; ids look like ``TCK-0001``."""
        key = (tenant_id, incident_id)
        existing = self._tickets.get(key)
        ticket_id = existing.id if existing else f"TCK-{len(self._tickets) + 1:04d}"
        self._tickets[key] = Ticket(ticket_id, incident_id, title, body)
        return ticket_id

    def get(self, tenant_id: str, incident_id: str) -> Ticket | None:
        """Return the incident's ticket, if any."""
        return self._tickets.get((tenant_id, incident_id))
