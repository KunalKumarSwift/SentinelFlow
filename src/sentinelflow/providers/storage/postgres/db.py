"""Three query helpers so repositories contain SQL and mapping, nothing else.

Each call borrows a connection for one transaction: committed on success, rolled back
on error. Rows come back as dicts and are decoded with ``rows`` accessors.
"""

from collections.abc import Sequence
from typing import LiteralString

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from sentinelflow.providers.storage.postgres.rows import Row

Params = Sequence[object]


def fetch_one(pool: ConnectionPool, sql: LiteralString, params: Params) -> Row | None:
    """Return the first row of ``sql``, or ``None``."""
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(pool: ConnectionPool, sql: LiteralString, params: Params) -> list[Row]:
    """Return every row of ``sql``."""
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def execute(pool: ConnectionPool, sql: LiteralString, params: Params) -> int:
    """Run a write statement and return the number of rows it affected."""
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount
