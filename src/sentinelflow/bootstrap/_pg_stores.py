"""PostgreSQL-backed stores (``STORAGE_BACKEND=postgres``)."""

from sentinelflow.bootstrap._stores import Stores
from sentinelflow.contracts.run_queue import RunQueue
from sentinelflow.core.clock import Clock
from sentinelflow.providers.storage.postgres.checkpointer import open_checkpointer
from sentinelflow.providers.storage.postgres.pg_alerts import PgAlertRepository
from sentinelflow.providers.storage.postgres.pg_approvals import PgApprovalRepository
from sentinelflow.providers.storage.postgres.pg_audit import PgAuditStore
from sentinelflow.providers.storage.postgres.pg_incidents import PgIncidentRepository
from sentinelflow.providers.storage.postgres.pg_runs import PgRunRepository
from sentinelflow.providers.storage.postgres.pool import apply_schema, open_pool
from sentinelflow.providers.ticketing.pg_ticketing import PgTicketing


def postgres_stores(clock: Clock, url: str, queue: RunQueue) -> Stores:
    """Open pools, create missing tables and return Postgres-backed stores."""
    pool = open_pool(url)
    apply_schema(pool)
    return Stores(
        clock=clock,
        alerts=PgAlertRepository(pool),
        incidents=PgIncidentRepository(pool),
        approvals=PgApprovalRepository(pool),
        runs=PgRunRepository(pool),
        audit=PgAuditStore(pool),
        checkpointer=open_checkpointer(url),
        ticketing=PgTicketing(pool),
        queue=queue,
    )
