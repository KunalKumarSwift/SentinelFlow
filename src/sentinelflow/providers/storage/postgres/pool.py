"""Connection pool and schema set-up for the PostgreSQL storage backend."""

from pathlib import Path

from psycopg_pool import ConnectionPool

_SCHEMA = Path(__file__).with_name("schema.sql")
# Arbitrary constant naming "SentinelFlow schema set-up" among advisory locks.
SCHEMA_LOCK = 0x5E17_0001


def open_pool(url: str, max_size: int = 10) -> ConnectionPool:
    """Open a thread-safe pool; API threads and the worker share it."""
    return ConnectionPool(url, min_size=1, max_size=max_size, open=True)


def apply_schema(pool: ConnectionPool) -> None:
    """Create any missing tables and indexes (idempotent, safe on every start-up).

    Concurrent ``create ... if not exists`` statements race inside PostgreSQL's catalog,
    so processes starting together (API + workers) take turns under an advisory lock.
    """
    with pool.connection() as conn:
        conn.execute("select pg_advisory_xact_lock(%s)", (SCHEMA_LOCK,))
        conn.execute(_SCHEMA.read_text(encoding="utf-8").encode())
