"""Tests for the background worker loop and runtime configuration checks."""

import threading

import pytest
from pydantic import SecretStr

from sentinelflow.bootstrap.serve import work_until
from sentinelflow.bootstrap.wiring import build_runtime
from sentinelflow.core.config import Settings


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


def test_unsupported_backend_fails_at_start_up() -> None:
    settings = Settings(  # type: ignore[call-arg]
        jwt_secret=SecretStr("s" * 32), queue_backend="redis"
    )
    with pytest.raises(ValueError, match="Phase 1"):
        build_runtime(settings)
