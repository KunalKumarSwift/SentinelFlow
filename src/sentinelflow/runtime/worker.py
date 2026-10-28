"""Worker loop: claim commands, run them, then ack, leave for retry, or dead-letter.

Failure policy:

* ``ProviderError(retryable=True)`` or an unexpected exception → leave unacked so the
  queue redelivers it, until ``max_attempts`` is reached → dead-letter.
* Any other ``SentinelFlowError`` (not found, denied, invalid) is deterministic and
  will fail again → dead-letter immediately.
"""

from collections.abc import Callable

from sentinelflow.contracts.run_queue import Delivery, RunQueue, StartRun
from sentinelflow.domain.errors import ProviderError, SentinelFlowError

BATCH_SIZE = 10


class Worker:
    """Processes queued ``StartRun`` commands with one handler."""

    def __init__(
        self,
        queue: RunQueue,
        handler: Callable[[StartRun], None],
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
        try:
            self._handler(delivery.command)
        # Broad on purpose: this boundary classifies every failure as retry or dead-letter.
        except Exception as exc:
            self._on_failure(delivery, exc)
            return
        self._queue.ack(delivery)

    def _on_failure(self, delivery: Delivery, exc: Exception) -> None:
        if not _is_retryable(exc):
            self._queue.dead_letter(delivery, str(exc))
        elif delivery.attempt >= self._max_attempts:
            reason = f"gave up after {delivery.attempt} attempts: {exc}"
            self._queue.dead_letter(delivery, reason)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, ProviderError):
        return exc.retryable
    return not isinstance(exc, SentinelFlowError)
