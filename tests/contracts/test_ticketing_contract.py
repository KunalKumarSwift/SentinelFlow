"""Contract for ticketing providers: one ticket per incident, upserted."""

from collections.abc import Callable

import pytest

from sentinelflow.contracts.ticketing import TicketingProvider
from sentinelflow.providers.ticketing.memory_ticketing import MemoryTicketing
from sentinelflow.providers.ticketing.pg_ticketing import PgTicketing
from tests.contracts.pg import fresh_pool

IMPLEMENTATIONS: list[Callable[[], TicketingProvider]] = [
    MemoryTicketing,
    lambda: PgTicketing(fresh_pool()),
]


@pytest.fixture(params=IMPLEMENTATIONS)
def tickets(request: pytest.FixtureRequest) -> TicketingProvider:
    return request.param()


def test_upsert_creates_then_updates_one_ticket_per_incident(tickets: TicketingProvider) -> None:
    first = tickets.upsert("acme", "inc-1", "title", "v1")
    second = tickets.upsert("acme", "inc-1", "title", "v2")
    ticket = tickets.get("acme", "inc-1")
    assert first == second and ticket is not None and ticket.body == "v2"


def test_tickets_are_tenant_scoped(tickets: TicketingProvider) -> None:
    tickets.upsert("acme", "inc-1", "t", "b")
    assert tickets.get("globex", "inc-1") is None
