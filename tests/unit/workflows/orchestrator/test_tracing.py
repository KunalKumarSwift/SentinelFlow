"""Each lifecycle step runs in a span named after it, tagged with run and tenant."""

import pytest
from langgraph.errors import GraphInterrupt
from opentelemetry.trace import StatusCode

from sentinelflow.workflows.orchestrator.state import LifecycleState, LifecycleUpdate
from sentinelflow.workflows.orchestrator.tracing import traced
from tests.fakes.spans import span_recorder

STATE: LifecycleState = {
    "run_id": "run-1",
    "tenant_id": "acme",
    "incident_id": "inc-1",
    "alert_id": "alt-1",
}


def _raising(error: Exception):
    def step(state: LifecycleState) -> LifecycleUpdate:
        raise error

    return step


def test_step_runs_inside_a_tagged_span() -> None:
    tracer, spans = span_recorder()
    update = traced(tracer, "triage", lambda state: {"approval_ids": ["a"]})(STATE)
    [span] = spans.get_finished_spans()
    assert update == {"approval_ids": ["a"]}
    assert span.name == "lifecycle.triage"
    assert span.attributes == {"run_id": "run-1", "tenant_id": "acme", "incident_id": "inc-1"}


def test_pausing_for_approval_is_not_an_error() -> None:
    tracer, spans = span_recorder()
    with pytest.raises(GraphInterrupt):
        traced(tracer, "await_decisions", _raising(GraphInterrupt()))(STATE)
    [span] = spans.get_finished_spans()
    assert span.status.status_code is StatusCode.UNSET
    assert span.attributes is not None and span.attributes["interrupted"] is True


def test_a_failing_step_marks_its_span_as_error() -> None:
    tracer, spans = span_recorder()
    with pytest.raises(RuntimeError):
        traced(tracer, "contain", _raising(RuntimeError("boom")))(STATE)
    [span] = spans.get_finished_spans()
    assert span.status.status_code is StatusCode.ERROR
