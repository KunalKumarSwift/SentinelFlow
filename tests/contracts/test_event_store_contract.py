"""Contract for event stores: related events by shared entity, tenant and time window."""

from collections.abc import Callable, Iterable
from datetime import timedelta

import pytest

from sentinelflow.contracts.event_store import EventQuery, EventStore
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.providers.events.memory_event_store import MemoryEventStore
from tests.builders import T0

Factory = Callable[[Iterable[SecurityEvent]], EventStore]
IMPLEMENTATIONS: list[Factory] = [MemoryEventStore]


def _event(n: int, minutes: int, tenant: str = "acme", **entities: str) -> SecurityEvent:
    at = T0 + timedelta(minutes=minutes)
    return SecurityEvent(f"evt-{n}", tenant, at, "login_failed", Entities(**entities))


EVENTS = [
    _event(1, 0, user="alice"),
    _event(2, 5, ip="203.0.113.9"),
    _event(3, 10, user="bob"),
    _event(4, 600, user="alice"),
    _event(5, 1, tenant="globex", user="alice"),
]


@pytest.fixture(params=IMPLEMENTATIONS)
def store(request: pytest.FixtureRequest) -> EventStore:
    factory: Factory = request.param
    return factory(EVENTS)


def test_returns_events_sharing_any_entity_within_window_in_time_order(store: EventStore) -> None:
    query = EventQuery(
        "acme", Entities(user="alice", ip="203.0.113.9"), T0, T0 + timedelta(hours=1)
    )
    assert [e.id for e in store.related_events(query)] == ["evt-1", "evt-2"]


def test_query_without_entities_returns_nothing(store: EventStore) -> None:
    query = EventQuery("acme", Entities(), T0, T0 + timedelta(days=1))
    assert store.related_events(query) == []
