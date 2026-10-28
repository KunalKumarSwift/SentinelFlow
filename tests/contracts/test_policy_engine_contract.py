"""Every policy engine (in-code and OPA/Rego) gives the same decision and reason."""

from collections.abc import Callable

import pytest

from sentinelflow.security.permissions import Permission as Perm
from sentinelflow.security.policy import AccessRequest, ActionContext, Decision, PolicyEngine
from sentinelflow.security.policy_engine import InCodePolicyEngine
from tests.contracts.opa_backend import opa_engine
from tests.unit.security.policy_helpers import incident, request, who
from tests.unit.security.rbac_spec import EXPECTED

ENGINES: list[Callable[[], PolicyEngine]] = [InCodePolicyEngine, opa_engine]
CMDR = who("incident-commander", subject="u-cmdr")
L1 = who("soc-analyst-l1")
OK = ActionContext(target_user="alice", proposer="svc-orch", initiator="u-ana")

CASES: list[tuple[AccessRequest, Decision]] = [
    (request(L1, Perm.INCIDENT_READ), Decision(True, "granted by role soc-analyst-l1")),
    (
        request(who("auditor"), Perm.INCIDENT_READ, incident(tenant="globex")),
        Decision(False, "resource belongs to another tenant"),
    ),
    (request(L1, Perm.INCIDENT_CLOSE), Decision(False, "missing permission incident:close")),
    (
        request(L1, Perm.INCIDENT_READ, incident(team="soc-apac")),
        Decision(False, "resource belongs to team soc-apac"),
    ),
    (
        request(CMDR, Perm.INCIDENT_READ, incident(team="soc-apac")),
        Decision(True, "granted by role incident-commander"),
    ),
    (request(CMDR, Perm.ACTION_APPROVE_HIGH), Decision(False, "approval requires action context")),
    (
        request(CMDR, Perm.ACTION_APPROVE_HIGH, action=ActionContext(target_user="u-cmdr")),
        Decision(False, "cannot approve an action against yourself"),
    ),
    (
        request(CMDR, Perm.ACTION_APPROVE_HIGH, action=ActionContext(proposer="u-cmdr")),
        Decision(False, "separation of duties: proposer/initiator cannot approve"),
    ),
    (
        request(
            CMDR,
            Perm.ACTION_APPROVE_HIGH,
            action=ActionContext(prior_approvers=frozenset({"u-cmdr"})),
        ),
        Decision(False, "you have already decided on this approval"),
    ),
    (
        request(CMDR, Perm.ACTION_APPROVE_HIGH, action=ActionContext(approval_open=False)),
        Decision(False, "approval is no longer open"),
    ),
    (
        request(CMDR, Perm.ACTION_APPROVE_HIGH, action=OK),
        Decision(True, "granted by role incident-commander"),
    ),
    (
        request(who("orchestrator"), Perm.ACTION_EXECUTE, action=ActionContext()),
        Decision(False, "approval quorum not met"),
    ),
    (
        request(who("orchestrator"), Perm.ACTION_EXECUTE, action=ActionContext(quorum_met=True)),
        Decision(True, "granted by role orchestrator"),
    ),
]


@pytest.fixture(params=ENGINES, ids=["in-code", "opa"])
def engine(request: pytest.FixtureRequest) -> PolicyEngine:
    factory: Callable[[], PolicyEngine] = request.param
    return factory()


@pytest.mark.parametrize(("access", "expected"), CASES)
def test_decision_and_reason(
    engine: PolicyEngine, access: AccessRequest, expected: Decision
) -> None:
    assert engine.evaluate(access) == expected


def test_rbac_matrix(engine: PolicyEngine) -> None:
    # Approval/execution context that passes every ABAC rule, so only RBAC decides.
    ctx = ActionContext(target_user="alice", proposer="svc", initiator="svc", quorum_met=True)
    for role, granted in EXPECTED.items():
        for perm in Perm:
            allowed = engine.evaluate(request(who(role), perm, action=ctx)).allowed
            assert allowed is (perm.value in granted), (role, perm)
