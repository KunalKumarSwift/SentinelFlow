"""LangGraph checkpointer on PostgreSQL, so any worker can resume any paused run."""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool


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
    saver.setup()
    return saver
