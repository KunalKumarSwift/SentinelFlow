"""A worker that dies mid-run loses nothing: another worker resumes from the checkpoint.

The first worker crashes after triage was checkpointed (the event store blows up during
investigation, standing in for a killed process). Its command is never acked, so after
the visibility timeout a second worker claims it, continues at investigation and pauses
for approvals, without repeating triage.
"""

from collections.abc import Sequence
from dataclasses import replace
from datetime import timedelta

from sentinelflow.contracts.event_store import EventQuery
from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.domain.runs import RunStatus
from sentinelflow.providers.events.memory_event_store import MemoryEventStore
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.runtime.dispatch import Dispatcher
from sentinelflow.runtime.resume_handler import ResumeRunHandler
from sentinelflow.runtime.start_handler import StartRunHandler
from sentinelflow.runtime.worker import Worker
from sentinelflow.simulator.registry import SCENARIOS
from sentinelflow.workflows.investigation import InvestigationDeps, build_investigation_graph
from sentinelflow.workflows.orchestrator import build_lifecycle_graph
from tests.integration.lifecycle_harness import Harness
from tests.unit.simulator.conftest import make_context

TIMEOUT = timedelta(seconds=60)


class DiesOnce:
    """Event store whose first query fails like a killed worker process would."""

    def __init__(self, inner: MemoryEventStore) -> None:
        self._inner, self.calls = inner, 0

    def related_events(self, query: EventQuery) -> Sequence[SecurityEvent]:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("worker killed mid-run")
        return self._inner.related_events(query)


def _worker(h: Harness, name: str, queue: MemoryRunQueue, events: DiesOnce) -> Worker:
    assert h.deps is not None
    investigation = build_investigation_graph(InvestigationDeps(events, h.deps.llm))
    # Both workers share the harness's checkpointer, as they would share Postgres.
    graph = build_lifecycle_graph(replace(h.deps, investigation=investigation), h.saver)
    handler = Dispatcher(
        StartRunHandler(h.runs, graph, h.clock), ResumeRunHandler(h.runs, graph, h.clock)
    )
    return Worker(queue, handler, name)


def test_unacked_run_is_finished_by_another_worker_from_its_checkpoint() -> None:
    h = Harness()
    run = h.build("brute_force")
    queue = MemoryRunQueue(h.clock, TIMEOUT)
    queue.publish(StartRun(run.id, "acme", "triage", run.incident_id, run.alert_id, "svc"))
    events = DiesOnce(MemoryEventStore(SCENARIOS["brute_force"](make_context()).events))
    assert _worker(h, "doomed", queue, events).run_once() == 1
    survivor = _worker(h, "survivor", queue, events)
    assert survivor.run_once() == 0  # still invisible: the doomed worker might be alive
    h.clock.advance(TIMEOUT)
    assert survivor.run_once() == 1
    record = h.runs.get("acme", run.id)
    assert record is not None and record.status is RunStatus.WAITING
    verbs = [e.verb for e in h.audit.read("acme", 0, 100)]
    assert verbs.count("incident.triaged") == 1 and "incident.investigated" in verbs
    assert len(h.approvals.pending("acme")) == 2
