"""Contracts for approval and run repositories."""

from collections.abc import Callable
from dataclasses import replace

import pytest

from sentinelflow.contracts.approvals import ApprovalRepository
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.domain.actions import ActionKind, ProposedAction
from sentinelflow.domain.approvals import (
    Approval,
    ApprovalDecision,
    ApprovalStatus,
    new_approval,
    record_decision,
)
from sentinelflow.domain.runs import RunRecord, RunStatus
from sentinelflow.domain.severity import Severity
from sentinelflow.providers.storage.memory_approvals import MemoryApprovalRepository
from sentinelflow.providers.storage.memory_runs import MemoryRunRepository
from sentinelflow.providers.storage.postgres.pg_approvals import PgApprovalRepository
from sentinelflow.providers.storage.postgres.pg_runs import PgRunRepository
from sentinelflow.security.system_principals import orchestrator_for
from tests.builders import T0
from tests.contracts.pg import fresh_pool

APPROVALS: list[Callable[[], ApprovalRepository]] = [
    MemoryApprovalRepository,
    lambda: PgApprovalRepository(fresh_pool()),
]
RUNS: list[Callable[[], RunRepository]] = [
    MemoryRunRepository,
    lambda: PgRunRepository(fresh_pool()),
]


def _approval(n: int, run: str = "run-1", tenant: str = "acme") -> Approval:
    action = ProposedAction(f"inc-1:a{n}", "inc-1", ActionKind.BLOCK_IP, "203.0.113.9", "r", "svc")
    return new_approval(f"apr-{n}", tenant, run, action, Severity.HIGH, T0)


@pytest.fixture(params=APPROVALS)
def approvals(request: pytest.FixtureRequest) -> ApprovalRepository:
    return request.param()


@pytest.fixture(params=RUNS)
def runs(request: pytest.FixtureRequest) -> RunRepository:
    return request.param()


def test_approvals_by_run_and_pending_per_tenant(approvals: ApprovalRepository) -> None:
    approvals.add(_approval(1))
    approvals.add(_approval(2, run="run-2"))
    approvals.add(_approval(3, tenant="globex"))
    approvals.update(replace(_approval(2, run="run-2"), status=ApprovalStatus.REJECTED))
    assert [a.id for a in approvals.for_run("acme", "run-1")] == ["apr-1"]
    assert [a.id for a in approvals.pending("acme")] == ["apr-1"]
    assert approvals.get("globex", "apr-1") is None


def test_duplicate_approval_is_rejected(approvals: ApprovalRepository) -> None:
    approvals.add(_approval(1))
    with pytest.raises(ValueError, match="exists"):
        approvals.add(_approval(1))


def test_run_round_trip_and_tenant_isolation(runs: RunRepository) -> None:
    record = RunRecord(
        "run-1", "acme", "triage", "inc-1", "alt-1", orchestrator_for("acme"), RunStatus.QUEUED, T0
    )
    runs.add(record)
    runs.update(replace(record, status=RunStatus.COMPLETED))
    stored = runs.get("acme", "run-1")
    assert stored is not None and stored.status is RunStatus.COMPLETED
    assert runs.get("globex", "run-1") is None


def test_updating_missing_records_is_rejected(
    approvals: ApprovalRepository, runs: RunRepository
) -> None:
    record = RunRecord(
        "run-9", "acme", "triage", "inc-1", "alt-1", orchestrator_for("acme"), RunStatus.QUEUED, T0
    )
    with pytest.raises(KeyError):
        approvals.update(_approval(9))
    with pytest.raises(KeyError):
        runs.update(record)


def test_approval_round_trip_keeps_action_and_decisions(approvals: ApprovalRepository) -> None:
    approval = _approval(1)
    approvals.add(approval)
    decided = record_decision(approval, ApprovalDecision("cmdr-1", True, "looks right", T0))
    approvals.update(decided)
    assert approvals.get("acme", "apr-1") == decided


def test_run_round_trip_keeps_initiator(runs: RunRepository) -> None:
    record = RunRecord(
        "run-1", "acme", "triage", "inc-1", "alt-1", orchestrator_for("acme"), RunStatus.QUEUED, T0
    )
    runs.add(record)
    assert runs.get("acme", "run-1") == record


def test_duplicate_run_is_rejected(runs: RunRepository) -> None:
    record = RunRecord(
        "run-1", "acme", "triage", "inc-1", "alt-1", orchestrator_for("acme"), RunStatus.QUEUED, T0
    )
    runs.add(record)
    with pytest.raises(ValueError, match="exists"):
        runs.add(record)
