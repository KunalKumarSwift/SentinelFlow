"""Each ABAC rule: one allow (None) and one deny case."""

from sentinelflow.security import abac_rules as rules
from sentinelflow.security.permissions import Permission as Perm
from sentinelflow.security.policy import ActionContext
from tests.unit.security.policy_helpers import incident, request, who

APPROVE = Perm.ACTION_APPROVE_HIGH
CMDR = who("incident-commander", subject="u-cmdr")


def test_same_tenant() -> None:
    assert rules.same_tenant(request(CMDR, Perm.INCIDENT_READ)) is None
    denied = rules.same_tenant(request(CMDR, Perm.INCIDENT_READ, incident(tenant="globex")))
    assert denied is not None and "another tenant" in denied.reason


def test_team_scope_allows_own_team_and_read_all() -> None:
    assert rules.team_scope(request(who("soc-analyst-l1"), Perm.INCIDENT_READ)) is None
    other = incident(team="soc-apac")
    assert rules.team_scope(request(CMDR, Perm.INCIDENT_READ, other)) is None


def test_team_scope_denies_other_team_without_read_all() -> None:
    denied = rules.team_scope(
        request(who("soc-analyst-l1"), Perm.INCIDENT_READ, incident(team="soc-apac"))
    )
    assert denied is not None and "soc-apac" in denied.reason


def test_no_self_action() -> None:
    other = ActionContext(target_user="alice")
    assert rules.no_self_action(request(CMDR, APPROVE, action=other)) is None
    mine = ActionContext(target_user="u-cmdr")
    denied = rules.no_self_action(request(CMDR, APPROVE, action=mine))
    assert denied is not None and "yourself" in denied.reason


def test_separation_of_duties() -> None:
    fine = ActionContext(proposer="svc-orch", initiator="u-ana")
    assert rules.separation_of_duties(request(CMDR, APPROVE, action=fine)) is None
    for ctx in (ActionContext(proposer="u-cmdr"), ActionContext(initiator="u-cmdr")):
        denied = rules.separation_of_duties(request(CMDR, APPROVE, action=ctx))
        assert denied is not None and "separation of duties" in denied.reason


def test_distinct_approvers() -> None:
    first = ActionContext(prior_approvers=frozenset({"u-other"}))
    assert rules.distinct_approvers(request(CMDR, APPROVE, action=first)) is None
    again = ActionContext(prior_approvers=frozenset({"u-cmdr"}))
    denied = rules.distinct_approvers(request(CMDR, APPROVE, action=again))
    assert denied is not None and "already" in denied.reason


def test_approval_still_open() -> None:
    assert rules.approval_still_open(request(CMDR, APPROVE, action=ActionContext())) is None
    closed = ActionContext(approval_open=False)
    denied = rules.approval_still_open(request(CMDR, APPROVE, action=closed))
    assert denied is not None and "no longer open" in denied.reason


def test_executed_only_if_approved() -> None:
    orch = who("orchestrator", subject="svc-orch")
    approved = ActionContext(quorum_met=True)
    assert (
        rules.executed_only_if_approved(request(orch, Perm.ACTION_EXECUTE, action=approved)) is None
    )
    denied = rules.executed_only_if_approved(
        request(orch, Perm.ACTION_EXECUTE, action=ActionContext())
    )
    assert denied is not None and "quorum" in denied.reason


def test_approval_rules_ignore_non_approval_requests() -> None:
    ctx = ActionContext(target_user="u-cmdr", proposer="u-cmdr", approval_open=False)
    req = request(CMDR, Perm.INCIDENT_READ, action=ctx)
    checks = (rules.no_self_action, rules.separation_of_duties, rules.approval_still_open)
    assert all(rule(req) is None for rule in checks)


def test_approval_rules_deny_when_action_context_missing() -> None:
    denied = rules.approval_still_open(request(CMDR, APPROVE))
    assert denied is not None and "context" in denied.reason
