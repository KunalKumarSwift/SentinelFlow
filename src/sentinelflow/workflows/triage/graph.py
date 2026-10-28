# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false
# LangGraph's builder/compile/invoke signatures contain partially unknown types under
# strict mode; this wiring file opts out of that one check. Nodes stay fully strict.
"""Wire the triage nodes into a LangGraph graph.

START ─┬─ lookup_ip ──┬─ score ── classify ── decide ── END
       └─ lookup_user ┘
"""

from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.triage import TriageResult
from sentinelflow.workflows.triage.deps import TriageDeps
from sentinelflow.workflows.triage.nodes.classify import make_classify
from sentinelflow.workflows.triage.nodes.decide import decide
from sentinelflow.workflows.triage.nodes.enrich import make_lookup_ip, make_lookup_user
from sentinelflow.workflows.triage.nodes.scan import scan_for_injection
from sentinelflow.workflows.triage.nodes.score import score
from sentinelflow.workflows.triage.state import TriageInput, TriageState

TriageGraph = CompiledStateGraph[TriageState, None, TriageInput, TriageState]


def build_triage_graph(deps: TriageDeps) -> TriageGraph:
    """Return the compiled triage graph using ``deps`` for all external calls."""
    graph = StateGraph(TriageState, input_schema=TriageInput)
    graph.add_node("scan", scan_for_injection)
    graph.add_node("lookup_ip", make_lookup_ip(deps))
    graph.add_node("lookup_user", make_lookup_user(deps))
    graph.add_node("score", score)
    graph.add_node("classify", make_classify(deps))
    graph.add_node("decide", decide)
    graph.add_edge(START, "scan")
    graph.add_edge("scan", "lookup_ip")
    graph.add_edge("scan", "lookup_user")
    graph.add_edge(["lookup_ip", "lookup_user"], "score")
    graph.add_edge("score", "classify")
    graph.add_edge("classify", "decide")
    graph.add_edge("decide", END)
    return graph.compile()


def run_triage(graph: TriageGraph, incident: Incident, alert: Alert) -> TriageResult:
    """Run triage for one incident and return its result."""
    final = graph.invoke({"incident": incident, "alert": alert})
    # invoke() is typed as returning dict[str, Any]; the graph always ends at decide.
    return cast(TriageResult, final["result"])
