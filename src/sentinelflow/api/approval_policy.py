"""Ask the policy engine whether a principal may decide an approval."""

from collections.abc import Mapping
from types import MappingProxyType

from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.actions import Impact, targets_user
from sentinelflow.domain.approvals import Approval, ApprovalStatus
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission
from sentinelflow.security.policy import AccessRequest, ActionContext, Decision, Resource

APPROVE_FOR: Mapping[Impact, Permission] = MappingProxyType(
    {
        Impact.LOW: Permission.ACTION_APPROVE_LOW,
        Impact.MEDIUM: Permission.ACTION_APPROVE_MEDIUM,
        Impact.HIGH: Permission.ACTION_APPROVE_HIGH,
    }
)


def decision_for(container: ApiContainer, principal: Principal, approval: Approval) -> Decision:
    """Evaluate tenant, RBAC (by impact) and every approval ABAC rule for ``principal``.

    Raises:
        NotFoundError: If the approval's incident or run no longer exists.
    """
    action = approval.action
    incident = container.incidents.get(approval.tenant_id, action.incident_id)
    run = container.runs.get(approval.tenant_id, approval.run_id)
    if incident is None or run is None:
        raise NotFoundError(f"approval {approval.id} refers to missing records")
    context = ActionContext(
        target_user=action.target if targets_user(action.kind) else None,
        proposer=action.proposed_by,
        initiator=run.initiator.subject,
        prior_approvers=approval.approvers,
        approval_open=approval.status is ApprovalStatus.PENDING,
    )
    resource = Resource("incident", incident.id, incident.tenant_id, incident.team)
    request = AccessRequest(principal, APPROVE_FOR[action.impact], resource, context)
    return container.policy.evaluate(request)
