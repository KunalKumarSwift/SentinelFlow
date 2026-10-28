"""Serialise an ``AccessRequest`` as the JSON ``input`` document the Rego policy reads."""

from sentinelflow.security.policy import AccessRequest, ActionContext


def to_input(request: AccessRequest) -> dict[str, object]:
    """Return the request as plain JSON values (sets become sorted lists)."""
    p, r = request.principal, request.resource
    return {
        "principal": {
            "subject": p.subject,
            "tenant_id": p.tenant_id,
            "team": p.team,
            "roles": sorted(p.roles),
            "kind": p.kind.value,
        },
        "permission": request.permission.value,
        "resource": {"kind": r.kind, "id": r.id, "tenant_id": r.tenant_id, "team": r.team},
        "action": None if request.action is None else _action(request.action),
    }


def _action(ctx: ActionContext) -> dict[str, object]:
    return {
        "target_user": ctx.target_user,
        "proposer": ctx.proposer,
        "initiator": ctx.initiator,
        "prior_approvers": sorted(ctx.prior_approvers),
        "approval_open": ctx.approval_open,
        "quorum_met": ctx.quorum_met,
    }
