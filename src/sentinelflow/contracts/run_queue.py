"""Interface of the durable queue between the API (control plane) and workers.

Delivery is at-least-once: a claimed command that is not acked within the visibility
timeout is delivered again, so handlers must be idempotent (checkpoints + keys).
Commands carry ids, never data; workers re-read current state from storage.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StartRun:
    """Ask a worker to run ``workflow`` for one incident."""

    run_id: str
    tenant_id: str
    workflow: str
    incident_id: str
    alert_id: str
    initiator: str


@dataclass(frozen=True, slots=True)
class Delivery:
    """One claimed copy of a queued command; ``attempt`` starts at 1."""

    id: str
    command: StartRun
    attempt: int


class RunQueue(Protocol):
    """At-least-once command queue with acknowledgement and a dead-letter list."""

    def publish(self, command: StartRun) -> None:
        """Enqueue ``command``."""
        ...

    def claim(self, consumer: str, max_items: int) -> Sequence[Delivery]:
        """Claim up to ``max_items`` available commands for ``consumer``."""
        ...

    def ack(self, delivery: Delivery) -> None:
        """Mark a delivery as done; it will not be delivered again."""
        ...

    def dead_letter(self, delivery: Delivery, reason: str) -> None:
        """Remove a delivery from circulation and keep it aside with ``reason``."""
        ...

    def dead_letters(self) -> Sequence[tuple[Delivery, str]]:
        """Return dead-lettered deliveries with their reasons, oldest first."""
        ...
