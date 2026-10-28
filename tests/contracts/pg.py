"""PostgreSQL backend for contract tests; skipped unless ``TEST_DATABASE_URL`` is set.

CI runs a Postgres service and sets the variable, so every contract test runs against
both the memory and the Postgres implementation there.
"""

import os
from functools import cache

import pytest
from psycopg_pool import ConnectionPool

from sentinelflow.providers.storage.postgres.pool import apply_schema, open_pool


@cache
def _shared_pool() -> ConnectionPool | None:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        return None
    pool = open_pool(url)
    apply_schema(pool)
    return pool


def fresh_pool() -> ConnectionPool:
    """Return the shared test pool with every table emptied, or skip the test."""
    pool = _shared_pool()
    if pool is None:
        pytest.skip("TEST_DATABASE_URL not set")
    with pool.connection() as conn:
        conn.execute("truncate incidents, alerts, approvals, workflow_runs, audit_events")
        # LangGraph's tables exist once a checkpointer has run setup(); empty them too.
        conn.execute(
            "do $$ begin if to_regclass('checkpoints') is not null then"
            " truncate checkpoints, checkpoint_blobs, checkpoint_writes; end if; end $$"
        )
    return pool


def database_url() -> str:
    """Return the test database URL after emptying every table, or skip the test."""
    fresh_pool()
    return os.environ["TEST_DATABASE_URL"]
