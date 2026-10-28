"""PostgreSQL run-record repository."""

from psycopg_pool import ConnectionPool

from sentinelflow.domain.runs import RunRecord, RunStatus
from sentinelflow.providers.storage.postgres.codecs import principal_from, principal_json
from sentinelflow.providers.storage.postgres.db import execute, fetch_one
from sentinelflow.providers.storage.postgres.rows import Row, json_record, moment, text

_INSERT = (
    "insert into workflow_runs (id, tenant_id, workflow, incident_id, alert_id, initiator,"
    " status, updated_at) values (%s, %s, %s, %s, %s, %s, %s, %s) on conflict do nothing"
)
_UPDATE = "update workflow_runs set status = %s, updated_at = %s where tenant_id = %s and id = %s"
_SELECT_ONE = "select * from workflow_runs where tenant_id = %s and id = %s"


class PgRunRepository:
    """Run records in ``workflow_runs``; ``id`` doubles as the LangGraph thread id."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Use ``pool`` for every query."""
        self._pool = pool

    def add(self, record: RunRecord) -> None:
        """Insert a new run record; an existing id raises ``ValueError``."""
        r = record
        params = (r.id, r.tenant_id, r.workflow, r.incident_id, r.alert_id)
        rest = (principal_json(r.initiator), r.status.value, r.updated_at)
        if execute(self._pool, _INSERT, params + rest) == 0:
            raise ValueError(f"run {r.id} already exists")

    def get(self, tenant_id: str, run_id: str) -> RunRecord | None:
        """Return the tenant's run record, if any."""
        row = fetch_one(self._pool, _SELECT_ONE, (tenant_id, run_id))
        return None if row is None else _record(row)

    def update(self, record: RunRecord) -> None:
        """Store the new status; an unknown id raises ``KeyError``."""
        r = record
        params = (r.status.value, r.updated_at, r.tenant_id, r.id)
        if execute(self._pool, _UPDATE, params) == 0:
            raise KeyError(f"run {r.id} does not exist")


def _record(row: Row) -> RunRecord:
    return RunRecord(
        id=text(row, "id"),
        tenant_id=text(row, "tenant_id"),
        workflow=text(row, "workflow"),
        incident_id=text(row, "incident_id"),
        alert_id=text(row, "alert_id"),
        initiator=principal_from(json_record(row, "initiator")),
        status=RunStatus(text(row, "status")),
        updated_at=moment(row, "updated_at"),
    )
