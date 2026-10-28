"""``sentinelflow-api``: serve the API, by default with a background worker thread.

    APP_ENV=dev JWT_SECRET=$(python -c 'print("x"*32)') uv run sentinelflow-api

Environment: everything in ``core/config.py``; ``API_HOST`` (default 127.0.0.1) and
``API_PORT`` (default 8000) choose the bind address. With ``RUN_WORKER_IN_API=false``
the process only serves HTTP and ``sentinelflow-worker`` processes do the work.
"""

import threading
from typing import Protocol

from sentinelflow.api.app import create_app
from sentinelflow.bootstrap.wiring import build_runtime
from sentinelflow.core.config import load_settings
from sentinelflow.core.logging import configure_logging

POLL_SECONDS = 0.5


class _Drainable(Protocol):
    def run_once(self) -> int: ...


def work_until(worker: _Drainable, stop: threading.Event) -> None:
    """Drain the queue until ``stop`` is set, pausing briefly when it is empty."""
    while not stop.is_set():
        if worker.run_once() == 0:
            stop.wait(POLL_SECONDS)


def main() -> None:  # pragma: no cover -- process entry point, covered by the README smoke run
    """Start the worker thread and serve HTTP until interrupted."""
    import uvicorn

    settings = load_settings()
    configure_logging(json_lines=settings.log_format == "json")
    runtime = build_runtime(settings)
    stop = threading.Event()
    thread = threading.Thread(target=work_until, args=(runtime.worker, stop), daemon=True)
    if settings.run_worker_in_api:
        thread.start()
    try:
        app = create_app(runtime.container)
        # Our middleware writes a structured access line, so uvicorn's own is off.
        uvicorn.run(app, host=settings.api_host, port=settings.api_port, access_log=False)
    finally:
        stop.set()
        if thread.is_alive():
            thread.join(timeout=5)
