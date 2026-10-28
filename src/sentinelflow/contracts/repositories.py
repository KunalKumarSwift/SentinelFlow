"""Storage interfaces for alerts and incidents.

Every read takes ``tenant_id`` explicitly so a query can never cross tenants by
accident; implementations must treat another tenant's data as non-existent.
"""

from dataclasses import dataclass
from typing import Protocol

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.incidents import Incident


@dataclass(frozen=True, slots=True)
class StoredAlert:
    """An alert together with its fingerprint and the incident it was grouped into."""

    alert: Alert
    fingerprint: str
    incident_id: str


class AlertRepository(Protocol):
    """Append-only store of ingested alerts."""

    def add(self, stored: StoredAlert) -> None:
        """Persist an ingested alert."""
        ...

    def latest_with_fingerprint(self, tenant_id: str, fingerprint: str) -> StoredAlert | None:
        """Return the most recently observed alert with ``fingerprint``, if any."""
        ...

    def get(self, tenant_id: str, alert_id: str) -> StoredAlert | None:
        """Return the stored alert, or ``None`` if absent or owned by another tenant."""
        ...


class IncidentRepository(Protocol):
    """Store of incidents, keyed by tenant and id."""

    def add(self, incident: Incident) -> None:
        """Persist a new incident. Raises ``ValueError`` if the id already exists."""
        ...

    def get(self, tenant_id: str, incident_id: str) -> Incident | None:
        """Return the incident, or ``None`` if absent or owned by another tenant."""
        ...

    def update(self, incident: Incident) -> None:
        """Replace a stored incident. Raises ``KeyError`` if it does not exist."""
        ...
