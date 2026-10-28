# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false
# LangGraph's builder/compile/invoke signatures contain partially unknown types under
# strict mode; this wiring file opts out of that one check. Nodes stay fully strict.
"""Wire the incident lifecycle: START -> triage -> apply_triage -> END.

Investigation, containment and reporting attach after ``apply_triage`` in Phase 2.
"""

from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.incidents import Incident
from sentinelflow.workflows.orchestrator.nodes import TriageStep, apply_triage_result
from sentinelflow.workflows.orchestrator.state import LifecycleInput, LifecycleState
from sentinelflow.workflows.triage.graph import TriageGraph

LifecycleGraph = CompiledStateGraph[LifecycleState, None, LifecycleInput, LifecycleState]


def build_lifecycle_graph(triage_graph: TriageGraph) -> LifecycleGraph:
    """Return the compiled lifecycle graph built around a compiled triage graph."""
    graph = StateGraph(LifecycleState, input_schema=LifecycleInput)
    graph.add_node("triage", TriageStep(triage_graph))
    graph.add_node("apply_triage", apply_triage_result)
    graph.add_edge(START, "triage")
    graph.add_edge("triage", "apply_triage")
    graph.add_edge("apply_triage", END)
    return graph.compile()


def run_lifecycle(graph: LifecycleGraph, incident: Incident, alert: Alert) -> Incident:
    """Run the lifecycle for one incident and return the updated incident."""
    final = graph.invoke({"incident": incident, "alert": alert})
    # invoke() is typed as returning dict[str, Any]; apply_triage always writes incident.
    return cast(Incident, final["incident"])
