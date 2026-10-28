"""Approval request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from sentinelflow.domain.approvals import Approval


class ApprovalOut(BaseModel):
    """An approval as shown to approvers."""

    id: str
    incident_id: str
    run_id: str
    action: str
    target: str
    impact: str
    required_role: str
    required_count: int
    decisions: int
    status: str
    expires_at: datetime

    @classmethod
    def of(cls, approval: Approval, target: str) -> "ApprovalOut":
        """Map a domain approval; ``target`` is already redacted for the caller."""
        action = approval.action
        return cls(
            id=approval.id,
            incident_id=action.incident_id,
            run_id=approval.run_id,
            action=action.kind.value,
            target=target,
            impact=action.impact.value,
            required_role=approval.required_role,
            required_count=approval.required_count,
            decisions=len(approval.decisions),
            status=approval.status.value,
            expires_at=approval.expires_at,
        )


class ApprovalPage(BaseModel):
    """Approvals the caller may decide."""

    items: list[ApprovalOut]


class DecisionIn(BaseModel):
    """Approve or reject, with a reason that goes into the audit log."""

    model_config = ConfigDict(extra="forbid")

    approved: bool
    reason: str = Field(min_length=5, max_length=500)
