"""LangGraph checkpointer on PostgreSQL, so any worker can resume any paused run."""

import time

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

# Arbitrary constant naming "checkpointer migrations" among advisory locks.
CHECKPOINT_LOCK = 0x5E17_0002
LOCK_POLL_SECONDS = 0.1


def open_checkpointer(url: str, max_size: int = 5) -> PostgresSaver:
    """Return a ready ``PostgresSaver`` with its tables created.

    The saver needs autocommit connections with dict rows and no server-side prepared
    statements, so it gets its own pool rather than sharing the repositories' one.
    """
    pool = ConnectionPool[Connection[DictRow]](
        url,
        min_size=1,
        max_size=max_size,
        open=True,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    saver = PostgresSaver(pool)
    with pool.connection() as conn:
        _acquire(conn)
        try:
            saver.setup()
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (CHECKPOINT_LOCK,))
    return saver


def _acquire(conn: Connection[DictRow]) -> None:
    # setup() runs migrations, so processes starting together must take turns. A blocking
    # pg_advisory_lock would deadlock: the migrations' CREATE INDEX CONCURRENTLY waits for
    # every open transaction, including a waiter blocked inside that lock call. Polling
    # with try-lock leaves waiters outside any transaction between attempts.
    while True:
        row = conn.execute("select pg_try_advisory_lock(%s) as ok", (CHECKPOINT_LOCK,)).fetchone()
        if row is not None and row["ok"]:
            return
        time.sleep(LOCK_POLL_SECONDS)
