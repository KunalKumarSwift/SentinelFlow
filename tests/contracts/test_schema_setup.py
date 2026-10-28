"""Schema set-up is safe when many processes start at once (API + N workers)."""

from concurrent.futures import ThreadPoolExecutor

from langgraph.checkpoint.postgres import PostgresSaver

from sentinelflow.providers.storage.postgres.checkpointer import open_checkpointer
from sentinelflow.providers.storage.postgres.pool import apply_schema
from tests.contracts.pg import database_url, fresh_pool

TABLES = "incidents, alerts, approvals, workflow_runs, audit_events, tickets"


def test_concurrent_schema_setup_on_an_empty_database_succeeds() -> None:
    pool = fresh_pool()
    with pool.connection() as conn:
        conn.execute(f"drop table if exists {TABLES}")
        conn.execute("drop sequence if exists ticket_seq")

    def setup(_: int) -> None:
        apply_schema(pool)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(setup, range(8)))
    with pool.connection() as conn:
        row = conn.execute("select count(*) from incidents").fetchone()
    assert row == (0,)


def test_concurrent_checkpointer_setup_on_an_empty_database_succeeds() -> None:
    url = database_url()
    with fresh_pool().connection() as conn:
        conn.execute(
            "drop table if exists checkpoints, checkpoint_blobs, checkpoint_writes,"
            " checkpoint_migrations"
        )

    def setup(_: int) -> PostgresSaver:
        return open_checkpointer(url, max_size=2)

    with ThreadPoolExecutor(max_workers=6) as executor:
        savers = list(executor.map(setup, range(6)))
    for saver in savers:
        saver.conn.close()  # type: ignore[union-attr] -- the saver holds our pool
