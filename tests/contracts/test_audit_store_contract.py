"""Contract for audit stores: append-only, per-tenant chains, paged reads."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import pytest

from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.domain.audit import AuditEventDraft
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.postgres.pg_audit import PgAuditStore
from sentinelflow.security.audit_chain import verify_chain
from tests.builders import T0
from tests.contracts.pg import fresh_pool

IMPLEMENTATIONS: list[Callable[[], AuditStore]] = [
    MemoryAuditStore,
    lambda: PgAuditStore(fresh_pool()),
]


@pytest.fixture(params=IMPLEMENTATIONS)
def store(request: pytest.FixtureRequest) -> AuditStore:
    return request.param()


def _draft(tenant: str = "acme", verb: str = "alert.ingested") -> AuditEventDraft:
    return AuditEventDraft(tenant, T0, "svc-sim", verb, "alt-1", "ok", {"k": "v"})


def test_appends_form_a_verifiable_chain_per_tenant(store: AuditStore) -> None:
    for verb in ("a", "b", "c"):
        store.append(_draft(verb=verb))
    store.append(_draft(tenant="globex"))
    acme = store.read("acme", after_seq=0, limit=10)
    assert [e.verb for e in acme] == ["a", "b", "c"]
    assert verify_chain("acme", acme).ok
    assert [e.seq for e in store.read("globex", after_seq=0, limit=10)] == [1]


def test_read_pages_by_sequence(store: AuditStore) -> None:
    for verb in ("a", "b", "c", "d"):
        store.append(_draft(verb=verb))
    assert [e.verb for e in store.read("acme", after_seq=1, limit=2)] == ["b", "c"]


def test_concurrent_appends_keep_the_chain_gap_free(store: AuditStore) -> None:
    def append(n: int) -> None:
        store.append(_draft(verb=f"v{n}"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(append, range(40)))
    events = store.read("acme", after_seq=0, limit=100)
    assert [e.seq for e in events] == list(range(1, 41))
    assert verify_chain("acme", events).ok


def test_stored_event_reads_back_unchanged(store: AuditStore) -> None:
    event = store.append(_draft())
    assert store.read("acme", after_seq=0, limit=1) == [event]
