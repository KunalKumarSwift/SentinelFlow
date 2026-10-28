"""Tests for the background worker loop and runtime configuration checks."""

import threading

from sentinelflow.bootstrap.serve import work_until


class CountingWorker:
    """Processes two batches, then sets ``stop`` on the third (empty) call."""

    def __init__(self, stop: threading.Event) -> None:
        self.calls, self._stop = 0, stop

    def run_once(self) -> int:
        self.calls += 1
        if self.calls == 3:
            self._stop.set()
            return 0
        return 1


def test_work_until_drains_until_stopped() -> None:
    stop = threading.Event()
    worker = CountingWorker(stop)
    work_until(worker, stop)
    assert worker.calls == 3
