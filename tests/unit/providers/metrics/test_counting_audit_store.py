"""The audit-store decorator counts every appended event by verb and changes nothing else."""

from sentinelflow.domain.audit import AuditEventDraft
from sentinelflow.providers.metrics.counting_audit_store import CountingAuditStore
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from tests.builders import T0
from tests.fakes.fake_metrics import RecordingMetrics


def test_appends_are_counted_and_stored() -> None:
    inner, metrics = MemoryAuditStore(), RecordingMetrics()
    store = CountingAuditStore(inner, metrics)
    event = store.append(AuditEventDraft("acme", T0, "u-1", "policy.denied", "api", "denied"))
    assert metrics.calls == [("audit_event", "policy.denied")]
    assert store.read("acme", 0, 10) == inner.read("acme", 0, 10) == [event]
