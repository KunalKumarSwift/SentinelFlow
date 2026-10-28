"""Connection pool and schema set-up for the PostgreSQL storage backend."""

from pathlib import Path

from psycopg_pool import ConnectionPool

_SCHEMA = Path(__file__).with_name("schema.sql")


def open_pool(url: str, max_size: int = 10) -> ConnectionPool:
    """Open a thread-safe pool; API threads and the worker share it."""
    return ConnectionPool(url, min_size=1, max_size=max_size, open=True)


def apply_schema(pool: ConnectionPool) -> None:
    """Create any missing tables and indexes (idempotent, safe on every start-up)."""
    with pool.connection() as conn:
        conn.execute(_SCHEMA.read_text(encoding="utf-8").encode())
