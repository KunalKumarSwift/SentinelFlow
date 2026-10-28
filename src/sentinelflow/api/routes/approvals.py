"""``GET /v1/approvals`` and ``POST /v1/approvals/{id}/decision``."""

from typing import Annotated

from fastapi import APIRouter, Depends

from sentinelflow.api.approval_policy import APPROVE_FOR, decision_for
from sentinelflow.api.approval_service import decide
from sentinelflow.api.auth import Auth
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.schemas.approvals import ApprovalOut, ApprovalPage, DecisionIn
from sentinelflow.domain.actions import targets_user
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.approvals import Approval
from sentinelflow.domain.errors import PolicyDeniedError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.rbac import permissions_of


def build_approvals_router(container: ApiContainer, auth: Auth) -> APIRouter:
    """Return the approvals router."""
    router = APIRouter(prefix="/v1/approvals", tags=["approvals"])

    @router.get("")
    def list_approvals(
        principal: Annotated[Principal, Depends(auth.current_principal)],
    ) -> ApprovalPage:
        """Pending approvals the caller is actually allowed to decide."""
        if not permissions_of(principal) & set(APPROVE_FOR.values()):
            container.recorder().record(
                principal, "policy.denied", "api", {"permission": "action:approve:*"}
            )
            raise PolicyDeniedError("missing permission action:approve:*")
        pending = container.approvals.pending(principal.tenant_id)
        mine = [a for a in pending if decision_for(container, principal, a).allowed]
        return ApprovalPage(items=[_out(a, principal) for a in mine])

    @router.post("/{approval_id}/decision")
    def decide_approval(
        approval_id: str,
        body: DecisionIn,
        principal: Annotated[Principal, Depends(auth.current_principal)],
    ) -> ApprovalOut:
        """Approve or reject; the policy engine checks role, team, SoD and self-action."""
        return _out(decide(container, principal, approval_id, body), principal)

    def _out(approval: Approval, principal: Principal) -> ApprovalOut:
        action = approval.action
        if not targets_user(action.kind):
            return ApprovalOut.of(approval, action.target)
        view = container.redactor.entities_for(principal, Entities(user=action.target))
        return ApprovalOut.of(approval, view["user"])

    return router
