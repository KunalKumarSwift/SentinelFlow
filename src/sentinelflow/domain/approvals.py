"""Approvals: human sign-off on a proposed action, with quorum, rejection and expiry."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from sentinelflow.domain.actions import ProposedAction, approval_requirement
from sentinelflow.domain.errors import ConflictError
from sentinelflow.domain.severity import Severity

APPROVAL_TTL = timedelta(hours=4)


class ApprovalStatus(StrEnum):
    """Where an approval stands."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """One person's approve/reject with a reason."""

    approver_id: str
    approved: bool
    reason: str
    decided_at: datetime


@dataclass(frozen=True, slots=True)
class Approval:
    """Sign-off required before ``action`` may be executed."""

    id: str
    tenant_id: str
    run_id: str
    action: ProposedAction
    required_role: str
    required_count: int
    expires_at: datetime
    decisions: tuple[ApprovalDecision, ...] = ()
    status: ApprovalStatus = ApprovalStatus.PENDING

    @property
    def approvers(self) -> frozenset[str]:
        """Everyone who has decided so far (approve or reject)."""
        return frozenset(d.approver_id for d in self.decisions)


def new_approval(
    approval_id: str,
    tenant_id: str,
    run_id: str,
    action: ProposedAction,
    severity: Severity,
    now: datetime,
) -> Approval:
    """Open an approval whose role and quorum come from the action catalogue."""
    requirement = approval_requirement(action.kind, severity)
    return Approval(
        approval_id,
        tenant_id,
        run_id,
        action,
        requirement.role,
        requirement.count,
        now + APPROVAL_TTL,
    )


def record_decision(approval: Approval, decision: ApprovalDecision) -> Approval:
    """Return ``approval`` with ``decision`` added and its status recomputed.

    Raises:
        ConflictError: If the approval is not pending or this person already decided.
    """
    if approval.status is not ApprovalStatus.PENDING:
        raise ConflictError(f"approval {approval.id} is {approval.status}, not pending")
    if decision.approver_id in approval.approvers:
        raise ConflictError(f"{decision.approver_id} already decided approval {approval.id}")
    decisions = (*approval.decisions, decision)
    return replace(
        approval, decisions=decisions, status=_status(decisions, approval.required_count)
    )


def expire_if_due(approval: Approval, now: datetime) -> Approval:
    """Return the approval marked EXPIRED if it is still pending at or after its expiry."""
    if approval.status is ApprovalStatus.PENDING and now >= approval.expires_at:
        return replace(approval, status=ApprovalStatus.EXPIRED)
    return approval


def _status(decisions: tuple[ApprovalDecision, ...], required: int) -> ApprovalStatus:
    if any(not d.approved for d in decisions):
        return ApprovalStatus.REJECTED
    if len(decisions) >= required:
        return ApprovalStatus.APPROVED
    return ApprovalStatus.PENDING
