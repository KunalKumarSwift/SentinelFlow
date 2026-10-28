"""Interface to the log/event store investigations search (a SIEM in production)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.events import SecurityEvent


@dataclass(frozen=True, slots=True)
class EventQuery:
    """Events of ``tenant_id`` in ``[start, end]`` sharing any entity value with ``entities``."""

    tenant_id: str
    entities: Entities
    start: datetime
    end: datetime


class EventStore(Protocol):
    """Read access to raw security events."""

    def related_events(self, query: EventQuery) -> Sequence[SecurityEvent]:
        """Return matching events ordered by time, then id."""
        ...
