# redis-py leaves **kwargs untyped.
# pyright: reportUnknownMemberType=false
"""Redis backend for contract tests; skipped unless ``TEST_REDIS_URL`` is set."""

import os

import pytest
from redis import Redis


def fresh_redis() -> Redis:
    """Return a client on an emptied test database, or skip the test."""
    url = os.environ.get("TEST_REDIS_URL")
    if not url:
        pytest.skip("TEST_REDIS_URL not set")
    client = Redis.from_url(url, decode_responses=True)
    client.flushdb()
    return client
