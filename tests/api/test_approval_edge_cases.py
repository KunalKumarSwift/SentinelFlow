"""Approval edge cases with a controllable clock and seeded records."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from sentinelflow.api.approval_policy import decision_for
from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.actions import ActionKind, ProposedAction
from sentinelflow.domain.approvals import ApprovalStatus, new_approval
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.runs import RunRecord, RunStatus
from sentinelflow.domain.severity import Severity
from sentinelflow.security.system_principals import orchestrator_for
from tests.api.conftest import TokenFor
from tests.builders import T0, an_incident
from tests.fakes.fake_clock import FakeClock
from tests.unit.security.policy_helpers import who

ACTION = ProposedAction(
    "inc-0001:disable_user", "inc-0001", ActionKind.DISABLE_USER, "alice", "r", "svc-orchestrator"
)


def _seed(container: ApiContainer, severity: Severity = Severity.HIGH) -> str:
    container.incidents.add(an_incident(severity=severity))
    initiator = orchestrator_for("acme")
    container.runs.add(
        RunRecord(
            "run-1", "acme", "triage", "inc-0001", "alt-0001", initiator, RunStatus.WAITING, T0
        )
    )
    container.approvals.add(new_approval("apr-1", "acme", "run-1", ACTION, severity, T0))
    return "apr-1"


def _decide(client: TestClient, auth: TokenFor) -> int:
    body = {"approved": True, "reason": "evidence reviewed"}
    response = client.post(
        "/v1/approvals/apr-1/decision", json=body, headers=auth("incident-commander")
    )
    return response.status_code


def test_expired_approval_cannot_be_decided(
    client: TestClient, auth: TokenFor, container: ApiContainer
) -> None:
    _seed(container)
    assert isinstance(container.clock, FakeClock)
    container.clock.advance(timedelta(hours=5))
    assert _decide(client, auth) == 403
    stored = container.approvals.get("acme", "apr-1")
    assert stored is not None and stored.status is ApprovalStatus.EXPIRED


def test_first_of_two_required_approvals_does_not_wake_the_run(
    client: TestClient, auth: TokenFor, container: ApiContainer
) -> None:
    _seed(container, Severity.CRITICAL)
    assert _decide(client, auth) == 200
    assert container.queue.claim("test", max_items=10) == []


def test_approval_with_missing_records_is_not_found(container: ApiContainer) -> None:
    container.approvals.add(new_approval("apr-9", "acme", "run-9", ACTION, Severity.HIGH, T0))
    approval = container.approvals.get("acme", "apr-9")
    assert approval is not None
    with pytest.raises(NotFoundError):
        decision_for(container, who("incident-commander"), approval)
