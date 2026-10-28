# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false
# LangGraph's builder/compile/invoke signatures contain partially unknown types under
# strict mode; this wiring file opts out of that one check. Steps stay fully strict.
"""Wire the lifecycle and provide typed start/resume entry points.

    START → triage ─┬─ (closed: false positive) → END
                    └─ investigate ─┬─ (no approvals) ───────────────────────┐
                                    └─ await_decisions ⟲ (pending) → contain ┴→ report → END

``thread_id = run_id`` so any worker can resume any run from the checkpointer.
"""

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from sentinelflow.domain.runs import RunRecord
from sentinelflow.workflows.orchestrator import routes
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.state import LifecycleState
from sentinelflow.workflows.orchestrator.steps.await_step import make_await_step
from sentinelflow.workflows.orchestrator.steps.contain_step import make_contain_step
from sentinelflow.workflows.orchestrator.steps.investigate_step import make_investigate_step
from sentinelflow.workflows.orchestrator.steps.report_step import make_report_step
from sentinelflow.workflows.orchestrator.steps.triage_step import make_triage_step

LifecycleGraph = CompiledStateGraph[LifecycleState, None, LifecycleState, LifecycleState]


def build_lifecycle_graph(
    deps: LifecycleDeps, checkpointer: BaseCheckpointSaver[str]
) -> LifecycleGraph:
    """Return the compiled lifecycle graph persisting checkpoints in ``checkpointer``."""
    graph = StateGraph(LifecycleState)
    graph.add_node("triage", make_triage_step(deps))
    graph.add_node("investigate", make_investigate_step(deps))
    graph.add_node("await_decisions", make_await_step(deps))
    graph.add_node("contain", make_contain_step(deps))
    graph.add_node("report", make_report_step(deps))
    graph.add_edge(START, "triage")
    graph.add_conditional_edges("triage", routes.after_triage(deps), ["investigate", END])
    graph.add_conditional_edges(
        "investigate", routes.after_investigation, ["await_decisions", "report"]
    )
    graph.add_conditional_edges(
        "await_decisions", routes.after_await(deps), ["await_decisions", "contain"]
    )
    graph.add_edge("contain", "report")
    graph.add_edge("report", END)
    return graph.compile(checkpointer=checkpointer)


def run_lifecycle(graph: LifecycleGraph, run: RunRecord) -> bool:
    """Start the lifecycle for ``run``; return True if it paused for approvals.

    Note:
        Queues deliver at least once. A thread that already exists is continued from its
        checkpoint (or left alone if finished) instead of being restarted.
    """
    config = _config(run.id)
    snapshot = graph.get_state(config)
    if snapshot.values:
        if snapshot.next:
            graph.invoke(None, config)
        return _waiting(graph, run.id)
    start: LifecycleState = {
        "run_id": run.id,
        "tenant_id": run.tenant_id,
        "incident_id": run.incident_id,
        "alert_id": run.alert_id,
    }
    graph.invoke(start, config)
    return _waiting(graph, run.id)


def resume_lifecycle(graph: LifecycleGraph, run_id: str) -> bool:
    """Wake a paused run so it re-reads approvals; return True if it is still waiting."""
    graph.invoke(Command(resume=True), _config(run_id))
    return _waiting(graph, run_id)


def _config(run_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": run_id}}


def _waiting(graph: LifecycleGraph, run_id: str) -> bool:
    return bool(graph.get_state(_config(run_id)).next)
