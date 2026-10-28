"""Every worker log line carries the run and tenant it is about."""

from datetime import timedelta

from sentinelflow.contracts.run_queue import RunCommand, StartRun
from sentinelflow.domain.errors import NotFoundError, ProviderError
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.runtime.worker import Worker
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_metrics import RecordingMetrics
from tests.fakes.log_capture import capture_logs

CMD = StartRun("run-1", "acme", "triage", "inc-1", "alt-1", "svc-orchestrator")


def _run(error: Exception | None) -> None:
    def handler(_: RunCommand) -> None:
        if error is not None:
            raise error

    queue = MemoryRunQueue(FakeClock(T0), timedelta(seconds=60))
    queue.publish(CMD)
    Worker(queue, handler, "w1").run_once()


def test_success_is_logged_with_run_and_tenant() -> None:
    with capture_logs() as logs:
        _run(None)
    [line] = logs.named("run.command.done")
    assert (line["run_id"], line["tenant_id"], line["command"], line["attempt"]) == (
        "run-1",
        "acme",
        "StartRun",
        1,
    )


def test_retry_and_dead_letter_are_logged() -> None:
    with capture_logs() as logs:
        _run(ProviderError("llm timeout", retryable=True))
        _run(NotFoundError("incident inc-1 not found"))
    assert logs.named("run.command.retry")[0]["error"] == "ProviderError"
    dead = logs.named("run.command.dead_lettered")[0]
    assert (dead["run_id"], dead["reason"]) == ("run-1", "incident inc-1 not found")


def test_outcomes_are_reported_as_metrics() -> None:
    metrics = RecordingMetrics()
    for error in (None, ProviderError("t", retryable=True), NotFoundError("gone")):

        def handler(_: RunCommand, error: Exception | None = error) -> None:
            if error is not None:
                raise error

        queue = MemoryRunQueue(FakeClock(T0), timedelta(seconds=60))
        queue.publish(CMD)
        Worker(queue, handler, "w1", metrics=metrics).run_once()
    outcomes = [call[2] for call in metrics.calls]
    assert outcomes == ["done", "retry", "dead_lettered"]
