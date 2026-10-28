"""PostgreSQL audit store: append-only, one hash chain per tenant."""

from collections.abc import Sequence

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from sentinelflow.domain.audit import AuditEvent, AuditEventDraft
from sentinelflow.providers.storage.postgres.db import fetch_all
from sentinelflow.providers.storage.postgres.rows import Row, integer, json_object, moment, text
from sentinelflow.security.audit_chain import chain_next

# A per-tenant advisory lock serialises appends so ``seq`` stays gap-free and the chain
# linear even with many API threads and workers writing at once.
_LOCK = "select pg_advisory_xact_lock(hashtext(%s))"
_LAST = "select * from audit_events where tenant_id = %s order by seq desc limit 1"
_INSERT = (
    "insert into audit_events (tenant_id, seq, at, actor, verb, resource, outcome, details,"
    " prev_hash, hash) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
_PAGE = "select * from audit_events where tenant_id = %s and seq > %s order by seq limit %s"


class PgAuditStore:
    """Audit events in ``audit_events``; there is deliberately no update or delete."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Use ``pool`` for every query."""
        self._pool = pool

    def append(self, draft: AuditEventDraft) -> AuditEvent:
        """Link ``draft`` to the end of its tenant's chain inside one transaction."""
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(_LOCK, (draft.tenant_id,))
            cur.execute(_LAST, (draft.tenant_id,))
            last = cur.fetchone()
            event = chain_next(None if last is None else _event(last), draft)
            cur.execute(_INSERT, _params(event))
            return event

    def read(self, tenant_id: str, after_seq: int, limit: int) -> Sequence[AuditEvent]:
        """Return up to ``limit`` events after ``after_seq``, in order."""
        rows = fetch_all(self._pool, _PAGE, (tenant_id, after_seq, limit))
        return [_event(row) for row in rows]


def _params(e: AuditEvent) -> tuple[object, ...]:
    return (
        e.tenant_id,
        e.seq,
        e.at,
        e.actor,
        e.verb,
        e.resource,
        e.outcome,
        Jsonb(dict(e.details)),
        e.prev_hash,
        e.hash,
    )


def _event(row: Row) -> AuditEvent:
    return AuditEvent(
        seq=integer(row, "seq"),
        tenant_id=text(row, "tenant_id"),
        at=moment(row, "at"),
        actor=text(row, "actor"),
        verb=text(row, "verb"),
        resource=text(row, "resource"),
        outcome=text(row, "outcome"),
        details=json_object(row, "details"),
        prev_hash=text(row, "prev_hash"),
        hash=text(row, "hash"),
    )
