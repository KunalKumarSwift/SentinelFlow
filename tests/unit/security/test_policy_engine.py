"""Tests for the deny-overrides policy engine."""

from sentinelflow.security.permissions import Permission as Perm
from sentinelflow.security.policy import ActionContext
from sentinelflow.security.policy_engine import InCodePolicyEngine
from tests.unit.security.policy_helpers import incident, request, who

ENGINE = InCodePolicyEngine()


def test_allows_with_reason_naming_the_role() -> None:
    decision = ENGINE.evaluate(request(who("soc-analyst-l1"), Perm.INCIDENT_READ))
    assert decision.allowed and decision.reason == "granted by role soc-analyst-l1"


def test_tenant_check_runs_before_rbac() -> None:
    decision = ENGINE.evaluate(
        request(who("auditor"), Perm.INCIDENT_READ, incident(tenant="globex"))
    )
    assert not decision.allowed and "another tenant" in decision.reason


def test_missing_permission_is_denied() -> None:
    decision = ENGINE.evaluate(
        request(who("soc-analyst-l2"), Perm.ACTION_APPROVE_HIGH, action=ActionContext())
    )
    assert not decision.allowed and decision.reason == "missing permission action:approve:high"


def test_abac_denies_even_with_permission() -> None:
    ctx = ActionContext(target_user="u-cmdr")
    cmdr = who("incident-commander", subject="u-cmdr")
    decision = ENGINE.evaluate(request(cmdr, Perm.ACTION_APPROVE_HIGH, action=ctx))
    assert not decision.allowed and "yourself" in decision.reason


def test_full_approval_is_allowed() -> None:
    ctx = ActionContext(target_user="alice", proposer="svc-orch", initiator="u-ana")
    cmdr = who("incident-commander", subject="u-cmdr")
    assert ENGINE.evaluate(request(cmdr, Perm.ACTION_APPROVE_HIGH, action=ctx)).allowed
