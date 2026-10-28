"""The dispatcher routes each command type to its handler."""

from sentinelflow.contracts.run_queue import ResumeRun, RunCommand, StartRun
from sentinelflow.runtime.dispatch import Dispatcher

START = StartRun("run-1", "acme", "triage", "inc-1", "alt-1", "svc")
RESUME = ResumeRun("run-1", "acme", "apr-1")


def test_routes_start_and_resume() -> None:
    seen: list[tuple[str, RunCommand]] = []
    dispatch = Dispatcher(lambda c: seen.append(("start", c)), lambda c: seen.append(("resume", c)))
    dispatch(START)
    dispatch(RESUME)
    assert seen == [("start", START), ("resume", RESUME)]
