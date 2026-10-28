"""Tests for the worker loop: ack on success, retry or dead-letter on failure."""

from datetime import timedelta

from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.domain.errors import NotFoundError, ProviderError
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.runtime.worker import Worker
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock

TIMEOUT = timedelta(seconds=60)
CMD = StartRun("run-1", "acme", "triage", "inc-1", "alt-1", "svc-orchestrator")


class ScriptedHandler:
    """Raises the scripted exceptions in order, then succeeds."""

    def __init__(self, *failures: Exception) -> None:
        self._failures = list(failures)
        self.handled: list[StartRun] = []

    def __call__(self, command: StartRun) -> None:
        self.handled.append(command)
        if self._failures:
            raise self._failures.pop(0)


def _setup(
    handler: ScriptedHandler, max_attempts: int = 3
) -> tuple[Worker, MemoryRunQueue, FakeClock]:
    clock = FakeClock(T0)
    queue = MemoryRunQueue(clock, TIMEOUT)
    queue.publish(CMD)
    return Worker(queue, handler, "w1", max_attempts=max_attempts), queue, clock


def test_successful_command_is_acked() -> None:
    worker, queue, clock = _setup(ScriptedHandler())
    assert worker.run_once() == 1
    clock.advance(TIMEOUT)
    assert queue.claim("w2", max_items=1) == []


def test_retryable_failure_is_left_for_redelivery() -> None:
    handler = ScriptedHandler(ProviderError("llm timeout", retryable=True))
    worker, _, clock = _setup(handler)
    worker.run_once()
    clock.advance(TIMEOUT)
    worker.run_once()
    assert handler.handled == [CMD, CMD]


def test_unexpected_exception_is_retried() -> None:
    handler = ScriptedHandler(RuntimeError("bug or outage"))
    worker, queue, clock = _setup(handler)
    worker.run_once()
    clock.advance(TIMEOUT)
    worker.run_once()
    assert len(handler.handled) == 2 and queue.dead_letters() == []


def test_permanent_failure_is_dead_lettered_immediately() -> None:
    worker, queue, _ = _setup(ScriptedHandler(NotFoundError("incident inc-1 not found")))
    worker.run_once()
    assert [reason for _, reason in queue.dead_letters()] == ["incident inc-1 not found"]


def test_too_many_attempts_are_dead_lettered() -> None:
    failures = [ProviderError("down", retryable=True) for _ in range(3)]
    worker, queue, clock = _setup(ScriptedHandler(*failures), max_attempts=3)
    for _ in range(3):
        worker.run_once()
        clock.advance(TIMEOUT)
    assert [reason for _, reason in queue.dead_letters()] == ["gave up after 3 attempts: down"]
