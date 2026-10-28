"""Three query helpers so repositories contain SQL and mapping, nothing else.

Each call borrows a connection for one transaction: committed on success, rolled back
on error. The transaction first sets ``app.tenant_id`` so row-level security confines it
to ``tenant_id``. Rows come back as dicts and are decoded with ``rows`` accessors.
"""

from collections.abc import Sequence
from typing import LiteralString

from psycopg import Cursor
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from sentinelflow.providers.storage.postgres.rows import Row

Params = Sequence[object]


def fetch_one(
    pool: ConnectionPool, tenant_id: str, sql: LiteralString, params: Params
) -> Row | None:
    """Return the first row of ``sql``, or ``None``."""
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        scope_to_tenant(cur, tenant_id)
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(
    pool: ConnectionPool, tenant_id: str, sql: LiteralString, params: Params
) -> list[Row]:
    """Return every row of ``sql``."""
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        scope_to_tenant(cur, tenant_id)
        cur.execute(sql, params)
        return list(cur.fetchall())


def execute(pool: ConnectionPool, tenant_id: str, sql: LiteralString, params: Params) -> int:
    """Run a write statement and return the number of rows it affected."""
    with pool.connection() as conn, conn.cursor() as cur:
        scope_to_tenant(cur, tenant_id)
        cur.execute(sql, params)
        return cur.rowcount


def scope_to_tenant[R](cur: Cursor[R], tenant_id: str) -> None:
    """Confine the current transaction to ``tenant_id`` (row-level security)."""
    cur.execute("select set_config('app.tenant_id', %s, true)", (tenant_id,))
