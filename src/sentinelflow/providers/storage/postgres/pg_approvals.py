"""PostgreSQL approval repository; the action and decisions live in jsonb columns."""

from collections.abc import Sequence

from psycopg_pool import ConnectionPool

from sentinelflow.domain.approvals import Approval, ApprovalStatus
from sentinelflow.providers.storage.postgres.codecs import (
    action_from,
    action_json,
    decision_from,
    decisions_json,
)
from sentinelflow.providers.storage.postgres.db import execute, fetch_all, fetch_one
from sentinelflow.providers.storage.postgres.rows import (
    Row,
    integer,
    json_record,
    json_records,
    moment,
    text,
)

_INSERT = (
    "insert into approvals (id, tenant_id, run_id, action, required_role, required_count,"
    " expires_at, decisions, status) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    " on conflict do nothing"
)
_UPDATE = (
    "update approvals set decisions = %s, status = %s, expires_at = %s"
    " where tenant_id = %s and id = %s"
)
_SELECT_ONE = "select * from approvals where tenant_id = %s and id = %s"
_SELECT_RUN = "select * from approvals where tenant_id = %s and run_id = %s order by seq"
_SELECT_PENDING = "select * from approvals where tenant_id = %s and status = 'pending' order by seq"


class PgApprovalRepository:
    """Approvals in the ``approvals`` table, keyed by (tenant_id, id)."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Use ``pool`` for every query."""
        self._pool = pool

    def add(self, approval: Approval) -> None:
        """Insert a new approval; an existing id raises ``ValueError``."""
        a = approval
        params = (a.id, a.tenant_id, a.run_id, action_json(a.action), a.required_role)
        rest = (a.required_count, a.expires_at, decisions_json(a.decisions), a.status.value)
        if execute(self._pool, _INSERT, params + rest) == 0:
            raise ValueError(f"approval {a.id} already exists")

    def get(self, tenant_id: str, approval_id: str) -> Approval | None:
        """Return the tenant's approval, if any."""
        row = fetch_one(self._pool, _SELECT_ONE, (tenant_id, approval_id))
        return None if row is None else _approval(row)

    def update(self, approval: Approval) -> None:
        """Store new decisions and status; an unknown id raises ``KeyError``."""
        a = approval
        params = (decisions_json(a.decisions), a.status.value, a.expires_at, a.tenant_id, a.id)
        if execute(self._pool, _UPDATE, params) == 0:
            raise KeyError(f"approval {a.id} does not exist")

    def for_run(self, tenant_id: str, run_id: str) -> Sequence[Approval]:
        """Return the run's approvals in creation order."""
        return [_approval(r) for r in fetch_all(self._pool, _SELECT_RUN, (tenant_id, run_id))]

    def pending(self, tenant_id: str) -> Sequence[Approval]:
        """Return the tenant's pending approvals in creation order."""
        return [_approval(r) for r in fetch_all(self._pool, _SELECT_PENDING, (tenant_id,))]


def _approval(row: Row) -> Approval:
    return Approval(
        id=text(row, "id"),
        tenant_id=text(row, "tenant_id"),
        run_id=text(row, "run_id"),
        action=action_from(json_record(row, "action")),
        required_role=text(row, "required_role"),
        required_count=integer(row, "required_count"),
        expires_at=moment(row, "expires_at"),
        decisions=tuple(decision_from(d) for d in json_records(row, "decisions")),
        status=ApprovalStatus(text(row, "status")),
    )
