"""Approval-request messages name what needs deciding, never who or what is targeted."""

from sentinelflow.domain.actions import ActionKind, ProposedAction
from sentinelflow.domain.approvals import new_approval
from sentinelflow.domain.notification import approval_request_message
from sentinelflow.domain.severity import Severity
from tests.builders import T0, an_incident


def test_message_lists_actions_and_roles_without_targets() -> None:
    incident = an_incident(severity=Severity.CRITICAL)
    actions = [
        ProposedAction("a1", incident.id, ActionKind.DISABLE_USER, "alice", "r", "svc"),
        ProposedAction("a2", incident.id, ActionKind.BLOCK_IP, "203.0.113.9", "r", "svc"),
    ]
    approvals = [
        new_approval(f"apr-{a.id}", "acme", "run-1", a, incident.severity, T0) for a in actions
    ]
    message = approval_request_message(incident, approvals)
    assert message == (
        "SentinelFlow: incident inc-0001 (CRITICAL) needs approval: "
        "disable_user [2 x incident-commander], block_ip [1 x soc-analyst-l2]"
    )
    assert "alice" not in message and "203.0.113.9" not in message
