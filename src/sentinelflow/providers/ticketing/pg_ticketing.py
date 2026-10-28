"""Tickets in PostgreSQL, so reports written by a worker are readable by every API process."""

from psycopg_pool import ConnectionPool

from sentinelflow.contracts.ticketing import Ticket
from sentinelflow.providers.storage.postgres.db import fetch_one
from sentinelflow.providers.storage.postgres.rows import text

_UPSERT = (
    "insert into tickets (tenant_id, incident_id, id, title, body)"
    " values (%s, %s, 'TCK-' || lpad(nextval('ticket_seq')::text, 4, '0'), %s, %s)"
    " on conflict (tenant_id, incident_id)"
    " do update set title = excluded.title, body = excluded.body returning id"
)
_SELECT = "select * from tickets where tenant_id = %s and incident_id = %s"


class PgTicketing:
    """One row per (tenant, incident); the id stays stable across upserts."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Use ``pool`` for every query."""
        self._pool = pool

    def upsert(self, tenant_id: str, incident_id: str, title: str, body: str) -> str:
        """Create or replace the incident's ticket and return its id."""
        row = fetch_one(self._pool, _UPSERT, (tenant_id, incident_id, title, body))
        assert row is not None  # noqa: S101 -- "returning" always yields a row
        return text(row, "id")

    def get(self, tenant_id: str, incident_id: str) -> Ticket | None:
        """Return the incident's ticket, if any."""
        row = fetch_one(self._pool, _SELECT, (tenant_id, incident_id))
        if row is None:
            return None
        return Ticket(text(row, "id"), incident_id, text(row, "title"), text(row, "body"))
