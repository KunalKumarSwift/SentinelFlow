"""In-process run queue with Redis-Streams-like redelivery semantics.

A claimed message becomes claimable again once ``visibility_timeout`` has passed
without an ack, which is how a crashed worker's work gets picked up by another.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

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

    def publish(self, command: RunCommand) -> None:
        """Enqueue ``command``."""
        self._next_id += 1
        self._entries[f"msg-{self._next_id:06d}"] = _Entry(command)

    def claim(self, consumer: str, max_items: int) -> Sequence[Delivery]:
        """Claim up to ``max_items`` unclaimed or timed-out messages, oldest first."""
        now = self._clock.now()
        claimed: list[Delivery] = []
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
        self._entries.pop(delivery.id, None)

    def dead_letter(self, delivery: Delivery, reason: str) -> None:
        """Move the message to the dead-letter list."""
        self._entries.pop(delivery.id, None)
        self._dead.append((delivery, reason))

    def dead_letters(self) -> Sequence[tuple[Delivery, str]]:
        """Return dead-lettered messages with reasons, oldest first."""
        return list(self._dead)
