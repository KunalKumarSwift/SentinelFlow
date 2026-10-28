"""Full incident lifecycle: triage → investigation → human approval → containment."""

from datetime import timedelta

from sentinelflow.domain.actions import ActionKind
from sentinelflow.domain.approvals import ApprovalStatus
from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.workflows.orchestrator import run_lifecycle
from tests.integration.lifecycle_harness import Harness
from tests.unit.security.policy_helpers import who


def _status(h: Harness) -> IncidentStatus:
    incident = h.incidents.get("acme", "inc-0001")
    assert incident is not None
    return incident.status


def test_false_positive_closes_without_approvals() -> None:
    h = Harness()
    assert h.start("benign_travel") is False
    assert _status(h) is IncidentStatus.CLOSED and h.approvals.pending("acme") == []


def test_attack_pauses_for_approval_with_catalogue_requirements() -> None:
    h = Harness()
    assert h.start("brute_force") is True
    assert _status(h) is IncidentStatus.AWAITING_APPROVAL
    pending = {a.action.kind: a.required_role for a in h.approvals.pending("acme")}
    assert pending == {
        ActionKind.DISABLE_USER: "incident-commander",
        ActionKind.BLOCK_IP: "soc-analyst-l2",
    }
    assert h.identity is not None and h.identity.applied == []


def test_resume_while_pending_keeps_waiting_and_executes_nothing() -> None:
    h = Harness()
    h.start("brute_force")
    first = h.approvals.pending("acme")[0]
    h.decide(first, "u-cmdr")
    assert h.resume() is True
    assert h.identity is not None and h.identity.applied == []


def test_all_approved_executes_and_contains() -> None:
    h = Harness()
    h.start("brute_force")
    for approval in h.approvals.pending("acme"):
        h.decide(approval, "u-cmdr")
    assert h.resume() is False
    assert _status(h) is IncidentStatus.CONTAINED
    assert h.identity is not None
    assert [a.kind for a in h.identity.applied] == [ActionKind.DISABLE_USER, ActionKind.BLOCK_IP]
    verbs = [e.verb for e in h.audit.read("acme", 0, 100)]
    assert verbs.count("tool.allowed") == 4 and "incident.contained" in verbs


def test_all_rejected_escalates_without_side_effects() -> None:
    h = Harness()
    h.start("brute_force")
    for approval in h.approvals.pending("acme"):
        h.decide(approval, "u-cmdr", approved=False)
    assert h.resume() is False
    assert _status(h) is IncidentStatus.ESCALATED
    assert h.identity is not None and h.identity.applied == []
    statuses = {a.status for a in h.approvals.for_run("acme", "run-1")}
    assert statuses == {ApprovalStatus.REJECTED}


def test_initiator_who_cannot_propose_gets_no_approvals_and_escalates() -> None:
    h = Harness()
    assert h.start("brute_force", initiator=who("executive")) is False
    assert _status(h) is IncidentStatus.ESCALATED
    denied = [e for e in h.audit.read("acme", 0, 100) if e.verb == "tool.denied"]
    assert len(denied) == 2


def test_duplicate_start_of_finished_run_is_a_no_op() -> None:
    h = Harness()
    h.start("benign_travel")
    run = h.runs.get("acme", "run-1")
    assert run is not None and h.graph is not None
    assert run_lifecycle(h.graph, run) is False
    assert _status(h) is IncidentStatus.CLOSED


def test_duplicate_start_while_waiting_stays_waiting_without_retriage() -> None:
    h = Harness()
    h.start("brute_force")
    run = h.runs.get("acme", "run-1")
    assert run is not None and h.graph is not None
    assert run_lifecycle(h.graph, run) is True
    verbs = [e.verb for e in h.audit.read("acme", 0, 100)]
    assert verbs.count("incident.triaged") == 1


def test_undecided_approvals_expire_and_the_incident_escalates() -> None:
    h = Harness()
    h.start("brute_force")
    h.clock.advance(timedelta(hours=4))
    assert h.resume() is False
    assert _status(h) is IncidentStatus.ESCALATED
    statuses = {a.status for a in h.approvals.for_run("acme", "run-1")}
    assert statuses == {ApprovalStatus.EXPIRED}
