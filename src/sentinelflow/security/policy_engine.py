"""In-code policy engine: tenant check, then RBAC, then ABAC rules; first deny wins."""

from collections.abc import Sequence

from sentinelflow.security.abac_rules import DEFAULT_RULES, Rule, same_tenant
from sentinelflow.security.policy import AccessRequest, Decision
from sentinelflow.security.roles import ROLE_PERMISSIONS


class InCodePolicyEngine:
    """``PolicyEngine`` backed by the role matrix and the ABAC rule functions."""

    def __init__(self, rules: Sequence[Rule] = DEFAULT_RULES) -> None:
        """Use ``rules`` after the tenant and RBAC checks."""
        self._rules = tuple(rules)

    def evaluate(self, request: AccessRequest) -> Decision:
        """Return allow/deny with a reason (deny overrides)."""
        tenant = same_tenant(request)
        if tenant is not None:
            return tenant
        role = _granting_role(request)
        if role is None:
            return Decision(False, f"missing permission {request.permission}")
        for rule in self._rules:
            denied = rule(request)
            if denied is not None:
                return denied
        return Decision(True, f"granted by role {role}")


def _granting_role(request: AccessRequest) -> str | None:
    roles = sorted(request.principal.roles)
    return next((r for r in roles if request.permission in ROLE_PERMISSIONS.get(r, ())), None)
