"""Contract for audit stores: append-only, per-tenant chains, paged reads."""

from collections.abc import Callable

import pytest

from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.domain.audit import AuditEventDraft
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.security.audit_chain import verify_chain
from tests.builders import T0

IMPLEMENTATIONS: list[Callable[[], AuditStore]] = [MemoryAuditStore]


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
