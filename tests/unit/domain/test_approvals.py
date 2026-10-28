"""Tests for approvals: quorum, rejection, expiry and duplicate decisions."""

from datetime import timedelta

import pytest

from sentinelflow.domain.actions import ActionKind, ProposedAction
from sentinelflow.domain.approvals import (
    Approval,
    ApprovalDecision,
    ApprovalStatus,
    expire_if_due,
    new_approval,
    record_decision,
)
from sentinelflow.domain.errors import ConflictError
from sentinelflow.domain.severity import Severity
from tests.builders import T0

ACTION = ProposedAction(
    "inc-1:disable_user", "inc-1", ActionKind.DISABLE_USER, "alice", "why", "svc"
)


def _approval(severity: Severity = Severity.HIGH) -> Approval:
    return new_approval("apr-1", "acme", "run-1", ACTION, severity, T0)


def _decide(who: str, approved: bool = True) -> ApprovalDecision:
    return ApprovalDecision(who, approved, "looks right", T0)


def test_new_approval_uses_catalogue_requirement_and_ttl() -> None:
    approval = _approval(Severity.CRITICAL)
    assert (approval.required_role, approval.required_count) == ("incident-commander", 2)
    assert approval.status is ApprovalStatus.PENDING
    assert approval.expires_at == T0 + timedelta(hours=4)


def test_single_approval_meets_quorum_of_one() -> None:
    assert record_decision(_approval(), _decide("u-a")).status is ApprovalStatus.APPROVED


def test_two_person_rule_needs_two_distinct_approvers() -> None:
    once = record_decision(_approval(Severity.CRITICAL), _decide("u-a"))
    assert once.status is ApprovalStatus.PENDING and once.approvers == frozenset({"u-a"})
    assert record_decision(once, _decide("u-b")).status is ApprovalStatus.APPROVED


def test_any_rejection_rejects() -> None:
    once = record_decision(_approval(Severity.CRITICAL), _decide("u-a"))
    assert record_decision(once, _decide("u-b", approved=False)).status is ApprovalStatus.REJECTED


def test_deciding_twice_or_after_closing_is_a_conflict() -> None:
    once = record_decision(_approval(Severity.CRITICAL), _decide("u-a"))
    with pytest.raises(ConflictError, match="already decided"):
        record_decision(once, _decide("u-a"))
    done = record_decision(_approval(), _decide("u-a"))
    with pytest.raises(ConflictError, match="not pending"):
        record_decision(done, _decide("u-b"))


def test_pending_approval_expires_after_ttl() -> None:
    approval = _approval()
    assert expire_if_due(approval, T0 + timedelta(hours=3)).status is ApprovalStatus.PENDING
    assert expire_if_due(approval, T0 + timedelta(hours=4)).status is ApprovalStatus.EXPIRED
    decided = record_decision(approval, _decide("u-a"))
    assert expire_if_due(decided, T0 + timedelta(days=1)) is decided
