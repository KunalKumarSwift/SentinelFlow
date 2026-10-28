"""In-memory incident store for tests and single-process mode."""

from sentinelflow.domain.incidents import Incident


class MemoryIncidentRepository:
    """Keeps incidents in a dict keyed by ``(tenant_id, incident_id)``."""

    def __init__(self) -> None:
        """Start empty."""
        self._items: dict[tuple[str, str], Incident] = {}

    def add(self, incident: Incident) -> None:
        """Store a new incident.

        Raises:
            ValueError: If an incident with the same tenant and id exists.
        """
        key = (incident.tenant_id, incident.id)
        if key in self._items:
            raise ValueError(f"incident {incident.id} already exists")
        self._items[key] = incident

    def get(self, tenant_id: str, incident_id: str) -> Incident | None:
        """Return the incident, or ``None`` if absent for this tenant."""
        return self._items.get((tenant_id, incident_id))

    def update(self, incident: Incident) -> None:
        """Replace a stored incident.

        Raises:
            KeyError: If the incident does not exist.
        """
        key = (incident.tenant_id, incident.id)
        if key not in self._items:
            raise KeyError(f"incident {incident.id} does not exist")
        self._items[key] = incident
