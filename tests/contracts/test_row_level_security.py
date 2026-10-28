"""PostgreSQL row-level security: even a query without a tenant filter sees only its tenant.

Defence in depth: repositories already filter by tenant; RLS makes the database refuse
cross-tenant rows if a query ever forgets to. (Run as a non-superuser: superusers
bypass RLS, which is why CI connects as a separate application role.)
"""

import psycopg
import pytest
from psycopg_pool import ConnectionPool

from sentinelflow.providers.storage.postgres.pg_incidents import PgIncidentRepository
from tests.builders import an_incident
from tests.contracts.pg import fresh_pool

TABLES = ("incidents", "alerts", "approvals", "workflow_runs", "audit_events", "tickets")


def _two_tenants() -> ConnectionPool:
    pool = fresh_pool()
    repo = PgIncidentRepository(pool)
    repo.add(an_incident(id="inc-a", tenant_id="acme"))
    repo.add(an_incident(id="inc-g", tenant_id="globex"))
    return pool


def _ids(pool: ConnectionPool, tenant: str | None) -> list[str]:
    with pool.connection() as conn:
        if tenant is not None:
            conn.execute("select set_config('app.tenant_id', %s, true)", (tenant,))
        rows = conn.execute("select id from incidents order by id").fetchall()
    return [str(row[0]) for row in rows]


def test_a_tenant_sees_only_its_own_rows_without_filtering() -> None:
    pool = _two_tenants()
    assert _ids(pool, "acme") == ["inc-a"]
    assert _ids(pool, "globex") == ["inc-g"]


def test_no_tenant_context_sees_nothing() -> None:
    assert _ids(_two_tenants(), None) == []


def test_writing_another_tenants_row_is_refused() -> None:
    pool = fresh_pool()
    with pytest.raises(psycopg.errors.InsufficientPrivilege), pool.connection() as conn:
        conn.execute("select set_config('app.tenant_id', 'acme', true)")
        conn.execute(
            "insert into tickets (tenant_id, incident_id, id, title, body)"
            " values ('globex', 'inc-1', 'TCK-9', 't', 'b')"
        )


def test_every_tenant_table_has_forced_row_level_security() -> None:
    with fresh_pool().connection() as conn:
        rows = conn.execute(
            "select relname, relrowsecurity, relforcerowsecurity from pg_class"
            " where relname = any(%s)",
            (list(TABLES),),
        ).fetchall()
    assert sorted(rows) == sorted((t, True, True) for t in TABLES)
