"""Builders for policy-engine requests."""

from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.security.permissions import Permission
from sentinelflow.security.policy import AccessRequest, ActionContext, Resource


def who(
    *roles: str, subject: str = "u-ana", tenant: str = "acme", team: str = "soc-emea"
) -> Principal:
    """Return a principal; services get the SERVICE kind."""
    kind = PrincipalKind.SERVICE if "orchestrator" in roles else PrincipalKind.USER
    return Principal(subject, tenant, team, frozenset(roles), kind)


def incident(tenant: str = "acme", team: str = "soc-emea") -> Resource:
    """Return an incident resource."""
    return Resource(kind="incident", id="inc-1", tenant_id=tenant, team=team)


def request(
    principal: Principal,
    permission: Permission,
    resource: Resource | None = None,
    action: ActionContext | None = None,
) -> AccessRequest:
    """Return an access request against an incident of team soc-emea by default."""
    return AccessRequest(principal, permission, resource or incident(), action)
