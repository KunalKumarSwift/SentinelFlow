"""Notification texts. They leave the system, so they name the decision, never targets.

User names, IPs and hosts stay behind the API's permission and pseudonymisation rules;
an approver follows the incident id into SentinelFlow to see them.
"""

from collections.abc import Iterable

from sentinelflow.domain.approvals import Approval
from sentinelflow.domain.incidents import Incident


def approval_request_message(incident: Incident, approvals: Iterable[Approval]) -> str:
    """Return the chat message announcing that ``approvals`` await a decision."""
    wanted = ", ".join(
        f"{a.action.kind.value} [{a.required_count} x {a.required_role}]" for a in approvals
    )
    return (
        f"SentinelFlow: incident {incident.id} ({incident.severity.name}) needs approval: {wanted}"
    )
