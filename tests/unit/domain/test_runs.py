"""Tests for run records."""

from datetime import timedelta

from sentinelflow.domain.runs import RunRecord, RunStatus, with_status
from sentinelflow.security.system_principals import orchestrator_for
from tests.builders import T0


def test_with_status_returns_updated_copy() -> None:
    record = RunRecord(
        "run-1", "acme", "triage", "inc-1", "alt-1", orchestrator_for("acme"), RunStatus.QUEUED, T0
    )
    later = T0 + timedelta(minutes=1)
    updated = with_status(record, RunStatus.WAITING, later)
    assert (record.status, updated.status, updated.updated_at) == (
        RunStatus.QUEUED,
        RunStatus.WAITING,
        later,
    )
