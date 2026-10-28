"""StartRunHandler drives the lifecycle for a queued run and records its status."""

import pytest

from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.runs import RunStatus
from sentinelflow.runtime.start_handler import StartRunHandler
from tests.integration.lifecycle_harness import Harness


def _command(run_id: str = "run-1") -> StartRun:
    return StartRun(run_id, "acme", "triage", "inc-0001", "alt-1", "svc-orchestrator")


def test_attack_run_ends_waiting_for_approval() -> None:
    h = Harness()
    h.build("brute_force")
    StartRunHandler(h.runs, h.graph_for("brute_force"), h.clock)(_command())
    record = h.runs.get("acme", "run-1")
    assert record is not None and record.status is RunStatus.WAITING


def test_false_positive_run_completes() -> None:
    h = Harness()
    h.build("benign_travel")
    StartRunHandler(h.runs, h.graph_for("benign_travel"), h.clock)(_command())
    record = h.runs.get("acme", "run-1")
    assert record is not None and record.status is RunStatus.COMPLETED


def test_unknown_run_is_a_permanent_error() -> None:
    h = Harness()
    h.build("brute_force")
    with pytest.raises(NotFoundError, match="run"):
        StartRunHandler(h.runs, h.graph_for("brute_force"), h.clock)(_command("run-404"))
