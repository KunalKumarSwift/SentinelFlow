"""``sentinelflow-worker``: needs a shared queue and stops cleanly on SIGTERM."""

import os
import signal
import threading
from collections.abc import Iterator

import pytest
from pydantic import SecretStr

from sentinelflow.bootstrap.worker_main import install_stop_signals, run_worker
from sentinelflow.core.config import Settings
from tests.contracts.pg import database_url

SECRET = SecretStr("s" * 32)


@pytest.fixture
def restore_signals() -> Iterator[None]:
    saved = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
    yield
    for sig, handler in saved.items():
        signal.signal(sig, handler)


def test_worker_refuses_a_process_local_queue() -> None:
    settings = Settings(jwt_secret=SECRET)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="QUEUE_BACKEND=redis"):
        run_worker(settings, threading.Event())


@pytest.mark.usefixtures("restore_signals")
def test_sigterm_sets_the_stop_event() -> None:
    stop = threading.Event()
    install_stop_signals(stop)
    signal.raise_signal(signal.SIGTERM)
    assert stop.is_set()


def test_worker_returns_once_stopped() -> None:
    url = database_url()
    redis_url = os.environ.get("TEST_REDIS_URL") or pytest.skip("TEST_REDIS_URL not set")
    settings = Settings(  # type: ignore[call-arg]
        jwt_secret=SECRET,
        storage_backend="postgres",
        database_url=SecretStr(url),
        queue_backend="redis",
        redis_url=redis_url,
        run_worker_in_api=False,
    )
    stop = threading.Event()
    stop.set()
    run_worker(settings, stop)
