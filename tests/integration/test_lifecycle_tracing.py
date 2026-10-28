"""A traced lifecycle run emits one span per step it executed."""

from dataclasses import replace

from langgraph.checkpoint.memory import InMemorySaver

from sentinelflow.workflows.orchestrator import build_lifecycle_graph, run_lifecycle
from tests.fakes.spans import span_recorder
from tests.integration.lifecycle_harness import Harness


def test_brute_force_run_is_traced_until_it_pauses() -> None:
    tracer, spans = span_recorder()
    h = Harness()
    run = h.build("brute_force")
    assert h.deps is not None
    graph = build_lifecycle_graph(replace(h.deps, tracer=tracer), InMemorySaver())
    assert run_lifecycle(graph, run) is True
    names = [s.name for s in spans.get_finished_spans()]
    assert names == ["lifecycle.triage", "lifecycle.investigate", "lifecycle.await_decisions"]
