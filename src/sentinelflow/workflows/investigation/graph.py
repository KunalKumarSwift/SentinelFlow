# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false
# LangGraph's builder/compile/invoke signatures contain partially unknown types under
# strict mode; this wiring file opts out of that one check. Nodes stay fully strict.
"""Wire the investigation: START -> fetch -> summarize -> analyse -> select -> END."""

from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.investigation import InvestigationResult
from sentinelflow.workflows.investigation.deps import InvestigationDeps
from sentinelflow.workflows.investigation.nodes.analyse import make_analyse
from sentinelflow.workflows.investigation.nodes.gather import make_fetch, summarize
from sentinelflow.workflows.investigation.nodes.select import select
from sentinelflow.workflows.investigation.state import InvestigationInput, InvestigationState

InvestigationGraph = CompiledStateGraph[
    InvestigationState, None, InvestigationInput, InvestigationState
]


def build_investigation_graph(deps: InvestigationDeps) -> InvestigationGraph:
    """Return the compiled investigation graph."""
    graph = StateGraph(InvestigationState, input_schema=InvestigationInput)
    graph.add_node("fetch", make_fetch(deps))
    graph.add_node("summarize", summarize)
    graph.add_node("analyse", make_analyse(deps))
    graph.add_node("select", select)
    graph.add_edge(START, "fetch")
    graph.add_edge("fetch", "summarize")
    graph.add_edge("summarize", "analyse")
    graph.add_edge("analyse", "select")
    graph.add_edge("select", END)
    return graph.compile()


def run_investigation(
    graph: InvestigationGraph, incident: Incident, alert: Alert
) -> InvestigationResult:
    """Investigate one incident and return the validated result."""
    final = graph.invoke({"incident": incident, "alert": alert})
    # invoke() is typed as returning dict[str, Any]; select always writes result.
    return cast(InvestigationResult, final["result"])
