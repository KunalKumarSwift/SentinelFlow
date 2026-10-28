"""OPA client: sends the request as input, reads the decision, and fails closed."""

import json

import httpx
import pytest

from sentinelflow.security.opa_engine import DECISION_PATH, OpaPolicyEngine
from sentinelflow.security.permissions import Permission as Perm
from sentinelflow.security.policy import ActionContext, Decision
from tests.unit.security.policy_helpers import request, who

REQUEST = request(
    who("incident-commander", subject="u-cmdr"),
    Perm.ACTION_APPROVE_HIGH,
    action=ActionContext(target_user="alice", prior_approvers=frozenset({"u-b", "u-a"})),
)


def _engine(handler: httpx.MockTransport) -> OpaPolicyEngine:
    return OpaPolicyEngine("http://opa:8181", transport=handler)


def test_request_is_sent_as_opa_input_and_decision_is_returned() -> None:
    seen: list[httpx.Request] = []

    def handle(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(
            200, json={"result": {"allowed": True, "reason": "granted by role x"}}
        )

    assert _engine(httpx.MockTransport(handle)).evaluate(REQUEST) == Decision(
        True, "granted by role x"
    )
    body = json.loads(seen[0].content)["input"]
    assert seen[0].url.path == f"/v1/data/{DECISION_PATH}"
    assert body["principal"] == {
        "subject": "u-cmdr",
        "tenant_id": "acme",
        "team": "soc-emea",
        "roles": ["incident-commander"],
        "kind": "user",
    }
    assert body["permission"] == "action:approve:high"
    assert body["resource"] == {
        "kind": "incident",
        "id": "inc-1",
        "tenant_id": "acme",
        "team": "soc-emea",
    }
    assert body["action"]["prior_approvers"] == ["u-a", "u-b"]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(200, json={}),
        httpx.Response(200, json={"result": {"allowed": "yes", "reason": "?"}}),
        httpx.Response(200, text="not json"),
    ],
)
def test_any_failure_denies(response: httpx.Response) -> None:
    decision = _engine(httpx.MockTransport(lambda _: response)).evaluate(REQUEST)
    assert decision == Decision(False, "policy engine unavailable")


def test_unreachable_server_denies() -> None:
    def refuse(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=req)

    assert not _engine(httpx.MockTransport(refuse)).evaluate(REQUEST).allowed


def test_no_action_context_is_sent_as_null() -> None:
    seen: list[dict[str, object]] = []

    def handle(req: httpx.Request) -> httpx.Response:
        seen.append(json.loads(req.content)["input"])
        return httpx.Response(200, json={"result": {"allowed": False, "reason": "r"}})

    _engine(httpx.MockTransport(handle)).evaluate(request(who("auditor"), Perm.AUDIT_READ))
    assert seen[0]["action"] is None
