"""End to end through the real wiring: alert → approvals → decisions → containment."""

import pytest

from tests.unit.bootstrap.flow import Flow, who

CMDR = who("u-cmdr", "incident-commander")
L2 = who("u-l2", "soc-analyst-l2")


@pytest.fixture
def flow() -> Flow:
    return Flow()


def test_full_approval_flow_contains_the_incident(flow: Flow) -> None:
    accepted = flow.ingest()
    pending = {a["action"]: a["id"] for a in flow.approvals(CMDR)}
    assert set(pending) == {"disable_user", "block_ip"}
    assert flow.decide(pending["disable_user"], CMDR) == 200
    assert flow.decide(pending["block_ip"], L2) == 200
    assert flow.runtime.worker.run_once() >= 1
    incident = flow.client.get(
        f"/v1/incidents/{accepted['incident_id']}", headers=flow.auth(L2)
    ).json()
    run = flow.client.get(f"/v1/runs/{accepted['run_id']}", headers=flow.auth(L2)).json()
    assert (incident["status"], run["status"]) == ("contained", "completed")


def test_l2_sees_only_what_it_may_approve_and_l1_none(flow: Flow) -> None:
    flow.ingest()
    assert [a["action"] for a in flow.approvals(L2)] == ["block_ip"]
    response = flow.client.get("/v1/approvals", headers=flow.auth(who("u-l1", "soc-analyst-l1")))
    assert response.status_code == 403


def test_l2_cannot_approve_high_impact(flow: Flow) -> None:
    flow.ingest()
    disable = next(a["id"] for a in flow.approvals(CMDR) if a["action"] == "disable_user")
    assert flow.decide(disable, L2) == 403


def test_commander_cannot_approve_action_against_themselves(flow: Flow) -> None:
    flow.ingest()
    approval = next(a for a in flow.approvals(CMDR) if a["action"] == "disable_user")
    target_commander = who(str(approval["target"]), "incident-commander")
    assert flow.decide(approval["id"], target_commander) == 403


def test_deciding_twice_is_denied(flow: Flow) -> None:
    flow.ingest()
    block = next(a["id"] for a in flow.approvals(L2) if a["action"] == "block_ip")
    assert flow.decide(block, L2) == 200
    assert flow.decide(block, L2) == 403


def test_other_tenant_cannot_see_or_decide(flow: Flow) -> None:
    flow.ingest()
    block = next(a["id"] for a in flow.approvals(L2) if a["action"] == "block_ip")
    other = who("u-x", "soc-analyst-l2", tenant="globex")
    assert flow.approvals(other) == []
    assert flow.decide(block, other) == 404


def test_rejection_escalates(flow: Flow) -> None:
    accepted = flow.ingest()
    for approval in flow.approvals(CMDR):
        flow.decide(approval["id"], CMDR, approved=False)
    flow.runtime.worker.run_once()
    incident = flow.client.get(
        f"/v1/incidents/{accepted['incident_id']}", headers=flow.auth(L2)
    ).json()
    assert incident["status"] == "escalated"


def test_unknown_run_is_404(flow: Flow) -> None:
    assert flow.client.get("/v1/runs/run-nope", headers=flow.auth(L2)).status_code == 404
