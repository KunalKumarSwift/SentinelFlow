"""Interface to the ticketing system that receives incident reports."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Ticket:
    """One ticket per incident."""

    id: str
    incident_id: str
    title: str
    body: str


class TicketingProvider(Protocol):
    """Creates and updates incident tickets."""

    def upsert(self, tenant_id: str, incident_id: str, title: str, body: str) -> str:
        """Create or replace the incident's ticket and return its id (stable per incident)."""
        ...

    def get(self, tenant_id: str, incident_id: str) -> Ticket | None:
        """Return the incident's ticket, or ``None`` if none exists for this tenant."""
        ...
