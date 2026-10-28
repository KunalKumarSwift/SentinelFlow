"""Attribute-based rules. Each returns a deny ``Decision`` or ``None`` (not applicable).

Approval rules apply only to ``action:approve:*`` requests and fail closed when the
action context is missing.
"""

from collections.abc import Callable

from sentinelflow.security.permissions import Permission
from sentinelflow.security.policy import AccessRequest, ActionContext, Decision
from sentinelflow.security.rbac import has_permission

Rule = Callable[[AccessRequest], Decision | None]
_APPROVE = frozenset(
    {
        Permission.ACTION_APPROVE_LOW,
        Permission.ACTION_APPROVE_MEDIUM,
        Permission.ACTION_APPROVE_HIGH,
    }
)
_MISSING = Decision(False, "approval requires action context")


def _deny(reason: str) -> Decision:
    return Decision(False, reason)


def same_tenant(req: AccessRequest) -> Decision | None:
    """Deny any request that crosses a tenant boundary."""
    if req.principal.tenant_id != req.resource.tenant_id:
        return _deny("resource belongs to another tenant")
    return None


def team_scope(req: AccessRequest) -> Decision | None:
    """Deny access to another team's resource unless the caller may read all teams."""
    team = req.resource.team
    if team is None or team == req.principal.team:
        return None
    if has_permission(req.principal, Permission.INCIDENT_READ_ALL):
        return None
    return _deny(f"resource belongs to team {team}")


def _approval(req: AccessRequest) -> ActionContext | Decision | None:
    if req.permission not in _APPROVE:
        return None
    return req.action or _MISSING


def no_self_action(req: AccessRequest) -> Decision | None:
    """Nobody approves an action against their own account."""
    ctx = _approval(req)
    if isinstance(ctx, ActionContext) and ctx.target_user == req.principal.subject:
        return _deny("cannot approve an action against yourself")
    return ctx if isinstance(ctx, Decision) else None


def separation_of_duties(req: AccessRequest) -> Decision | None:
    """The proposer or run initiator may not approve the same action."""
    ctx = _approval(req)
    if isinstance(ctx, ActionContext) and req.principal.subject in {ctx.proposer, ctx.initiator}:
        return _deny("separation of duties: proposer/initiator cannot approve")
    return ctx if isinstance(ctx, Decision) else None


def distinct_approvers(req: AccessRequest) -> Decision | None:
    """One person counts once towards a quorum."""
    ctx = _approval(req)
    if isinstance(ctx, ActionContext) and req.principal.subject in ctx.prior_approvers:
        return _deny("you have already decided on this approval")
    return ctx if isinstance(ctx, Decision) else None


def approval_still_open(req: AccessRequest) -> Decision | None:
    """Decided or expired approvals cannot be decided again."""
    ctx = _approval(req)
    if isinstance(ctx, ActionContext) and not ctx.approval_open:
        return _deny("approval is no longer open")
    return ctx if isinstance(ctx, Decision) else None


def executed_only_if_approved(req: AccessRequest) -> Decision | None:
    """Execution requires a met approval quorum."""
    if req.permission is not Permission.ACTION_EXECUTE:
        return None
    if req.action is None or not req.action.quorum_met:
        return _deny("approval quorum not met")
    return None


DEFAULT_RULES: tuple[Rule, ...] = (
    team_scope,
    no_self_action,
    separation_of_duties,
    distinct_approvers,
    approval_still_open,
    executed_only_if_approved,
)
