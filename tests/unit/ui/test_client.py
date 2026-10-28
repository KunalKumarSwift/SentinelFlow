"""The UI's API client, exercised against the real wired application."""

import httpx
import pytest

from sentinelflow.ui.client import ApiError, SentinelFlowClient, dev_token
from tests.unit.bootstrap.flow import Flow, who

CMDR = who("u-cmdr", "incident-commander")
L2 = who("u-l2", "soc-analyst-l2")
AUDITOR = who("u-aud", "auditor")


def _client(flow: Flow, identity: dict[str, object]) -> SentinelFlowClient:
    return SentinelFlowClient(flow.client, dev_token(flow.client, identity))


def test_incidents_and_approvals_are_listed() -> None:
    flow = Flow()
    flow.ingest()
    cmdr = _client(flow, dict(CMDR))
    [incident] = cmdr.incidents()
    assert (incident.status, incident.severity) == ("awaiting_approval", "high")
    assert {a.action for a in cmdr.approvals()} == {"disable_user", "block_ip"}


def test_deciding_through_the_client_contains_the_incident() -> None:
    flow = Flow()
    flow.ingest()
    cmdr, l2 = _client(flow, dict(CMDR)), _client(flow, dict(L2))
    by_action = {a.action: a.id for a in cmdr.approvals()}
    cmdr.decide(by_action["disable_user"], approved=True, reason="evidence reviewed")
    l2.decide(by_action["block_ip"], approved=True, reason="evidence reviewed")
    flow.runtime.worker.run_once()
    assert cmdr.incidents()[0].status == "closed"


def test_auditor_reads_and_verifies_the_chain() -> None:
    flow = Flow()
    flow.ingest()
    auditor = _client(flow, dict(AUDITOR))
    events = auditor.audit(after_seq=0, limit=100)
    assert events[0].seq == 1 and "alert.ingested" in {e.verb for e in events}
    assert auditor.verify().ok


def test_api_errors_carry_the_problem_detail() -> None:
    flow = Flow()
    l1 = _client(flow, dict(who("u-l1", "soc-analyst-l1")))
    with pytest.raises(ApiError, match="403") as caught:
        l1.approvals()
    assert caught.value.status == 403


def _fake(body: object) -> httpx.Client:
    response = httpx.Response(200, json=body)
    return httpx.Client(base_url="http://api", transport=httpx.MockTransport(lambda _: response))


def test_unexpected_response_shapes_are_errors_not_crashes() -> None:
    with pytest.raises(ApiError, match="unexpected response shape"):
        SentinelFlowClient(_fake(["not", "an", "object"]), "t").incidents()
    with pytest.raises(ApiError, match="no access token"):
        dev_token(_fake({"token": "x"}), {"subject": "u"})
