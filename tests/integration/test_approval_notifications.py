"""Approvers are notified when a run pauses; a broken notifier never breaks the run."""

from dataclasses import replace

from sentinelflow.domain.errors import ProviderError
from sentinelflow.workflows.orchestrator import build_lifecycle_graph, run_lifecycle
from tests.integration.lifecycle_harness import Harness


class Recording:
    def __init__(self, error: Exception | None = None) -> None:
        self.sent: list[tuple[str, str]] = []
        self._error = error

    def notify(self, channel: str, message: str) -> None:
        if self._error is not None:
            raise self._error
        self.sent.append((channel, message))


def _start(notifier: Recording) -> tuple[Harness, bool]:
    h = Harness()
    run = h.build("brute_force")
    assert h.deps is not None
    graph = build_lifecycle_graph(replace(h.deps, notifier=notifier), h.saver)
    return h, run_lifecycle(graph, run)


def test_pausing_for_approval_notifies_the_approvals_channel() -> None:
    notifier = Recording()
    _, waiting = _start(notifier)
    [(channel, message)] = notifier.sent
    assert waiting and channel == "approvals"
    assert "disable_user" in message and "block_ip" in message


def test_notification_failure_is_audited_and_the_run_still_waits() -> None:
    h, waiting = _start(Recording(ProviderError("webhook down", retryable=True)))
    verbs = [e.verb for e in h.audit.read("acme", 0, 100)]
    assert waiting and "notification.failed" in verbs
