"""Lifecycle nodes: run triage as a sub-workflow, then apply its result."""

from sentinelflow.domain.triage import apply_triage
from sentinelflow.workflows.orchestrator.state import LifecycleInput, LifecycleUpdate, TriagedInput
from sentinelflow.workflows.triage import run_triage
from sentinelflow.workflows.triage.graph import TriageGraph


class TriageStep:
    """Node that runs the compiled triage sub-workflow for the lifecycle's incident."""

    def __init__(self, triage_graph: TriageGraph) -> None:
        """Wrap a compiled triage graph."""
        self._graph = triage_graph

    def __call__(self, state: LifecycleInput) -> LifecycleUpdate:
        """Run triage and store its result."""
        return {"triage": run_triage(self._graph, state["incident"], state["alert"])}


def apply_triage_result(state: TriagedInput) -> LifecycleUpdate:
    """Write triage severity, verdict and status onto the incident."""
    return {"incident": apply_triage(state["incident"], state["triage"])}
