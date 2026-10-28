"""``sentinelflow-worker``: a worker process draining the shared run queue.

Run as many as needed next to API processes started with ``RUN_WORKER_IN_API=false``;
they coordinate only through PostgreSQL and Redis. SIGTERM finishes the current batch
and exits, so a rolling deploy never abandons a claimed command (and if one is killed
anyway, the command becomes visible again after the queue's visibility timeout).
"""

import signal
import threading

from sentinelflow.bootstrap.serve import work_until
from sentinelflow.bootstrap.wiring import build_runtime
from sentinelflow.core.config import Settings, load_settings


def install_stop_signals(stop: threading.Event) -> None:
    """Make SIGTERM and SIGINT request a graceful stop."""
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda _signum, _frame: stop.set())


def run_worker(settings: Settings, stop: threading.Event) -> None:
    """Process queued commands until ``stop`` is set.

    Raises:
        ValueError: If the queue is process-local, so a separate worker would never see work.
    """
    if settings.queue_backend != "redis":
        raise ValueError("sentinelflow-worker needs a shared queue: set QUEUE_BACKEND=redis")
    work_until(build_runtime(settings).worker, stop)


def main() -> None:  # pragma: no cover -- process entry point, exercised by Docker Compose
    """Run one worker process until it receives SIGTERM or SIGINT."""
    stop = threading.Event()
    install_stop_signals(stop)
    run_worker(load_settings(), stop)
