"""In-process run queue with the same redelivery semantics as ``RedisRunQueue``.

A claimed message becomes claimable again once ``visibility_timeout`` has passed
without an ack, which is how a crashed worker's work gets picked up by another.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock

from sentinelflow.contracts.run_queue import Delivery, RunCommand
from sentinelflow.core.clock import Clock


@dataclass(slots=True)
class _Entry:
    command: RunCommand
    attempts: int = 0
    claimed_at: datetime | None = None


class MemoryRunQueue:
    """Single-process ``RunQueue`` for tests and Phase 1."""

    def __init__(self, clock: Clock, visibility_timeout: timedelta) -> None:
        """Create an empty queue that redelivers after ``visibility_timeout``."""
        self._clock, self._timeout = clock, visibility_timeout
        self._entries: dict[str, _Entry] = {}
        self._dead: list[tuple[Delivery, str]] = []
        self._next_id = 0
        # The API thread publishes while the worker thread claims; one lock keeps the
        # dict consistent and a message from being claimed twice.
        self._lock = Lock()

    def publish(self, command: RunCommand) -> None:
        """Enqueue ``command``."""
        with self._lock:
            self._next_id += 1
            self._entries[f"msg-{self._next_id:06d}"] = _Entry(command)

    def claim(self, consumer: str, max_items: int) -> Sequence[Delivery]:
        """Claim up to ``max_items`` unclaimed or timed-out messages, oldest first."""
        now = self._clock.now()
        claimed: list[Delivery] = []
        with self._lock:
            for msg_id, entry in self._entries.items():
                if len(claimed) == max_items:
                    break
                if entry.claimed_at is None or now - entry.claimed_at >= self._timeout:
                    entry.attempts += 1
                    entry.claimed_at = now
                    claimed.append(Delivery(msg_id, entry.command, entry.attempts))
        return claimed

    def ack(self, delivery: Delivery) -> None:
        """Forget the message for good."""
        with self._lock:
            self._entries.pop(delivery.id, None)

    def dead_letter(self, delivery: Delivery, reason: str) -> None:
        """Move the message to the dead-letter list."""
        with self._lock:
            self._entries.pop(delivery.id, None)
            self._dead.append((delivery, reason))

    def depth(self) -> int:
        """Return how many messages are queued or in flight."""
        with self._lock:
            return len(self._entries)

    def dead_letters(self) -> Sequence[tuple[Delivery, str]]:
        """Return dead-lettered messages with reasons, oldest first."""
        return list(self._dead)
