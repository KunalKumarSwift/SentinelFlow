"""Record an approval decision: authorise, apply, audit, and wake the paused run."""

from sentinelflow.api.approval_policy import decision_for
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.schemas.approvals import DecisionIn
from sentinelflow.contracts.run_queue import ResumeRun
from sentinelflow.domain.approvals import (
    Approval,
    ApprovalDecision,
    ApprovalStatus,
    expire_if_due,
    record_decision,
)
from sentinelflow.domain.errors import NotFoundError, PolicyDeniedError
from sentinelflow.domain.principals import Principal


def decide(
    container: ApiContainer, principal: Principal, approval_id: str, body: DecisionIn
) -> Approval:
    """Apply ``principal``'s decision to the approval and return the updated approval.

    Raises:
        NotFoundError: Unknown approval (or another tenant's).
        PolicyDeniedError: The policy engine denied the decision (reason audited).
    """
    approval = _current(container, principal, approval_id)
    verdict = decision_for(container, principal, approval)
    if not verdict.allowed:
        details = {"approval": approval.id, "reason": verdict.reason}
        container.recorder().record(
            principal, "policy.denied", approval.action.incident_id, details
        )
        raise PolicyDeniedError(verdict.reason)
    decision = ApprovalDecision(
        principal.subject, body.approved, body.reason, container.clock.now()
    )
    updated = record_decision(approval, decision)
    container.approvals.update(updated)
    _audit_and_resume(container, principal, updated, body)
    return updated


def _current(container: ApiContainer, principal: Principal, approval_id: str) -> Approval:
    stored = container.approvals.get(principal.tenant_id, approval_id)
    if stored is None:
        raise NotFoundError(f"approval {approval_id} not found")
    current = expire_if_due(stored, container.clock.now())
    if current is not stored:
        container.approvals.update(current)
    return current


def _audit_and_resume(
    container: ApiContainer, principal: Principal, approval: Approval, body: DecisionIn
) -> None:
    details = {
        "approval": approval.id,
        "approved": str(body.approved),
        "reason": body.reason,
        "status": approval.status.value,
    }
    container.recorder().record(principal, "approval.decided", approval.action.incident_id, details)
    if approval.status is not ApprovalStatus.PENDING:
        container.queue.publish(ResumeRun(approval.run_id, approval.tenant_id, approval.id))
