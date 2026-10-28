"""Tests for the audit recorder helper."""

import pytest

from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.system_principals import orchestrator_for
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock


@pytest.mark.parametrize(
    ("verb", "outcome"),
    [("alert.ingested", "ok"), ("policy.denied", "denied"), ("run.failed", "failed")],
)
def test_record_stamps_actor_tenant_time_and_outcome(verb: str, outcome: str) -> None:
    store = MemoryAuditStore()
    event = AuditRecorder(store, FakeClock(T0)).record(
        orchestrator_for("acme"), verb, "inc-1", {"k": "v"}
    )
    assert (event.tenant_id, event.actor, event.at, event.outcome) == (
        "acme",
        "svc-orchestrator",
        T0,
        outcome,
    )
    assert store.read("acme", after_seq=0, limit=5) == [event]


def test_orchestrator_principal_is_a_service_with_orchestrator_role() -> None:
    principal = orchestrator_for("globex")
    assert (principal.tenant_id, principal.roles) == ("globex", frozenset({"orchestrator"}))
