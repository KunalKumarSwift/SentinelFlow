"""Worker loop: claim commands, run them, then ack, leave for retry, or dead-letter.

Failure policy:

* ``ProviderError(retryable=True)`` or an unexpected exception → leave unacked so the
  queue redelivers it, until ``max_attempts`` is reached → dead-letter.
* Any other ``SentinelFlowError`` (not found, denied, invalid) is deterministic and
  will fail again → dead-letter immediately.
"""

import time
from collections.abc import Callable

from sentinelflow.contracts.metrics import Metrics
from sentinelflow.contracts.run_queue import Delivery, RunCommand, RunQueue
from sentinelflow.core.logging import bound, get_logger
from sentinelflow.domain.errors import ProviderError, SentinelFlowError
from sentinelflow.providers.metrics.null_metrics import NullMetrics

BATCH_SIZE = 10
_log = get_logger("sentinelflow.worker")


class Worker:
    """Processes queued run commands with one handler (usually a ``Dispatcher``)."""

    def __init__(
        self,
        queue: RunQueue,
        handler: Callable[[RunCommand], None],
        consumer: str,
        *,
        max_attempts: int = 5,
        metrics: Metrics | None = None,
    ) -> None:
        """Create a worker identified as ``consumer`` on the queue."""
        self._queue, self._handler, self._consumer = queue, handler, consumer
        self._max_attempts = max_attempts
        self._metrics = metrics or NullMetrics()

    def run_once(self) -> int:
        """Claim and process one batch; return how many deliveries were processed."""
        deliveries = self._queue.claim(self._consumer, BATCH_SIZE)
        for delivery in deliveries:
            self._process(delivery)
        return len(deliveries)

    def _process(self, delivery: Delivery) -> None:
        command = delivery.command
        context = {"run_id": command.run_id, "tenant_id": command.tenant_id}
        started, name = time.perf_counter(), type(command).__name__
        with bound(**context, command=name, attempt=delivery.attempt):
            try:
                self._handler(command)
            # Broad on purpose: this boundary classifies every failure as retry or dead-letter.
            except Exception as exc:
                outcome = self._on_failure(delivery, exc)
            else:
                self._queue.ack(delivery)
                outcome = "done"
                _log.info("run.command.done")
        self._metrics.command_finished(name, outcome, time.perf_counter() - started)

    def _on_failure(self, delivery: Delivery, exc: Exception) -> str:
        if not _is_retryable(exc):
            self._dead_letter(delivery, str(exc))
        elif delivery.attempt >= self._max_attempts:
            self._dead_letter(delivery, f"gave up after {delivery.attempt} attempts: {exc}")
        else:
            _log.warning("run.command.retry", error=type(exc).__name__)
            return "retry"
        return "dead_lettered"

    def _dead_letter(self, delivery: Delivery, reason: str) -> None:
        self._queue.dead_letter(delivery, reason)
        _log.error("run.command.dead_lettered", reason=reason)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, ProviderError):
        return exc.retryable
    return not isinstance(exc, SentinelFlowError)
