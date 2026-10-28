"""ResumeRunHandler wakes a paused run and records the outcome."""

import pytest

from sentinelflow.contracts.run_queue import ResumeRun
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.runs import RunStatus
from sentinelflow.runtime.resume_handler import ResumeRunHandler
from tests.integration.lifecycle_harness import Harness


def test_resume_after_all_decisions_completes_the_run() -> None:
    h = Harness()
    h.start("brute_force")
    for approval in h.approvals.pending("acme"):
        h.decide(approval, "u-cmdr")
    ResumeRunHandler(h.runs, h.graph_for("brute_force"), h.clock)(
        ResumeRun("run-1", "acme", "apr-x")
    )
    record = h.runs.get("acme", "run-1")
    assert record is not None and record.status is RunStatus.COMPLETED


def test_resume_with_pending_approvals_keeps_waiting() -> None:
    h = Harness()
    h.start("brute_force")
    ResumeRunHandler(h.runs, h.graph_for("brute_force"), h.clock)(
        ResumeRun("run-1", "acme", "apr-x")
    )
    record = h.runs.get("acme", "run-1")
    assert record is not None and record.status is RunStatus.WAITING


def test_unknown_run_is_a_permanent_error() -> None:
    h = Harness()
    h.build("brute_force")
    with pytest.raises(NotFoundError, match="run"):
        ResumeRunHandler(h.runs, h.graph_for("brute_force"), h.clock)(
            ResumeRun("run-404", "acme", "a")
        )
