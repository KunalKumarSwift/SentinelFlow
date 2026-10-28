"""Worker loop: claim commands, run them, then ack, leave for retry, or dead-letter.

Failure policy:

* ``ProviderError(retryable=True)`` or an unexpected exception → leave unacked so the
  queue redelivers it, until ``max_attempts`` is reached → dead-letter.
* Any other ``SentinelFlowError`` (not found, denied, invalid) is deterministic and
  will fail again → dead-letter immediately.
"""

from collections.abc import Callable

from sentinelflow.contracts.run_queue import Delivery, RunCommand, RunQueue
from sentinelflow.core.logging import bound, get_logger
from sentinelflow.domain.errors import ProviderError, SentinelFlowError

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
    ) -> None:
        """Create a worker identified as ``consumer`` on the queue."""
        self._queue, self._handler, self._consumer = queue, handler, consumer
        self._max_attempts = max_attempts

    def run_once(self) -> int:
        """Claim and process one batch; return how many deliveries were processed."""
        deliveries = self._queue.claim(self._consumer, BATCH_SIZE)
        for delivery in deliveries:
            self._process(delivery)
        return len(deliveries)

    def _process(self, delivery: Delivery) -> None:
        command = delivery.command
        context = {"run_id": command.run_id, "tenant_id": command.tenant_id}
        with bound(**context, command=type(command).__name__, attempt=delivery.attempt):
            try:
                self._handler(command)
            # Broad on purpose: this boundary classifies every failure as retry or dead-letter.
            except Exception as exc:
                self._on_failure(delivery, exc)
                return
            self._queue.ack(delivery)
            _log.info("run.command.done")

    def _on_failure(self, delivery: Delivery, exc: Exception) -> None:
        if not _is_retryable(exc):
            self._dead_letter(delivery, str(exc))
        elif delivery.attempt >= self._max_attempts:
            self._dead_letter(delivery, f"gave up after {delivery.attempt} attempts: {exc}")
        else:
            _log.warning("run.command.retry", error=type(exc).__name__)

    def _dead_letter(self, delivery: Delivery, reason: str) -> None:
        self._queue.dead_letter(delivery, reason)
        _log.error("run.command.dead_lettered", reason=reason)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, ProviderError):
        return exc.retryable
    return not isinstance(exc, SentinelFlowError)
