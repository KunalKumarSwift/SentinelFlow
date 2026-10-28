"""Collect report facts from the incident, its approvals and its audit events."""

from sentinelflow.domain.actions import ActionKind, ProposedAction
from sentinelflow.domain.approvals import ApprovalDecision, new_approval, record_decision
from sentinelflow.domain.incidents import IncidentStatus, Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.system_principals import orchestrator_for
from sentinelflow.workflows.report.facts import collect_facts
from tests.builders import T0, an_incident
from tests.fakes.fake_clock import FakeClock

REDACTOR = Redactor(b"r" * 32)


def test_facts_come_from_audit_details_and_approvals() -> None:
    store, actor = MemoryAuditStore(), orchestrator_for("acme")
    recorder = AuditRecorder(store, FakeClock(T0))
    recorder.record(actor, "incident.triaged", "inc-0001", {"injection": "verdict_steering"})
    recorder.record(actor, "incident.investigated", "inc-0001", {"techniques": "T1110,T1078"})
    recorder.record(actor, "incident.contained", "inc-0001", {"executed": "inc-0001:disable_user"})
    recorder.record(actor, "incident.triaged", "inc-9999", {"injection": "other"})
    action = ProposedAction(
        "inc-0001:disable_user", "inc-0001", ActionKind.DISABLE_USER, "alice", "r", "svc"
    )
    approval = record_decision(
        new_approval("apr-1", "acme", "run-1", action, Severity.HIGH, T0),
        ApprovalDecision("u-cmdr", True, "ok", T0),
    )
    incident = an_incident(status=IncidentStatus.CONTAINED, verdict=Verdict.TRUE_POSITIVE)
    facts = collect_facts(incident, [approval], store.read("acme", 0, 50), REDACTOR)
    assert (facts.status, facts.severity, facts.verdict) == ("contained", "high", "true_positive")
    assert facts.injection == ("verdict_steering",)
    assert facts.techniques == ("T1110", "T1078")
    assert facts.executed == ("inc-0001:disable_user",)
    [line] = facts.actions
    assert (line.kind, line.status) == ("disable_user", "approved")
    assert line.target == REDACTOR.pseudonym("user", "alice")
