"""``sentinelflow-worker``: a worker process draining the shared run queue.

Run as many as needed next to API processes started with ``RUN_WORKER_IN_API=false``;
they coordinate only through PostgreSQL and Redis. SIGTERM finishes the current batch
and exits, so a rolling deploy never abandons a claimed command (and if one is killed
anyway, the command becomes visible again after the queue's visibility timeout).
"""

import signal
import threading
from collections.abc import Callable

from prometheus_client import start_http_server

from sentinelflow.bootstrap.serve import work_until
from sentinelflow.bootstrap.wiring import Runtime, build_runtime
from sentinelflow.core.config import Settings, load_settings
from sentinelflow.core.logging import configure_logging


def install_stop_signals(stop: threading.Event) -> None:
    """Make SIGTERM and SIGINT request a graceful stop."""
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda _signum, _frame: stop.set())


def run_worker(
    settings: Settings,
    stop: threading.Event,
    on_start: Callable[[Runtime], None] = lambda _runtime: None,
) -> None:
    """Process queued commands until ``stop`` is set; ``on_start`` sees the built runtime.

    Raises:
        ValueError: If the queue is process-local, so a separate worker would never see work.
    """
    if settings.queue_backend != "redis":
        raise ValueError("sentinelflow-worker needs a shared queue: set QUEUE_BACKEND=redis")
    runtime = build_runtime(settings)
    on_start(runtime)
    work_until(runtime.worker, stop)


def serve_metrics(runtime: Runtime, port: int) -> None:  # pragma: no cover -- binds a socket
    """Expose the worker's Prometheus metrics on ``port`` in a background thread."""
    start_http_server(port, registry=runtime.metrics.registry)


def main() -> None:  # pragma: no cover -- process entry point, exercised by Docker Compose
    """Run one worker process until it receives SIGTERM or SIGINT."""
    settings = load_settings()
    configure_logging(json_lines=settings.log_format == "json")
    stop = threading.Event()
    install_stop_signals(stop)
    run_worker(settings, stop, lambda runtime: serve_metrics(runtime, settings.metrics_port))
