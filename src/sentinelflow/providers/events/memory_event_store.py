"""In-memory event store serving a scenario's raw events."""

from collections.abc import Iterable, Sequence

from sentinelflow.contracts.event_store import EventQuery
from sentinelflow.domain.events import SecurityEvent


class MemoryEventStore:
    """Linear-scan ``EventStore``; fine for demo-sized data."""

    def __init__(self, events: Iterable[SecurityEvent] = ()) -> None:
        """Start with ``events``."""
        self._events = list(events)

    def related_events(self, query: EventQuery) -> Sequence[SecurityEvent]:
        """Return the tenant's events in the window that share an entity value."""
        wanted = set(query.entities.present().items())
        matches = [
            e
            for e in self._events
            if e.tenant_id == query.tenant_id
            and query.start <= e.at <= query.end
            and wanted & set(e.entities.present().items())
        ]
        return sorted(matches, key=lambda e: (e.at, e.id))
