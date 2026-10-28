# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false
# LangGraph's builder/compile/invoke signatures contain partially unknown types under
# strict mode; this wiring file opts out of that one check. Nodes stay fully strict.
"""Wire the access review: START → list_accounts → review → raise_findings → END."""

from dataclasses import dataclass
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from sentinelflow.domain.access_review import Finding
from sentinelflow.domain.incidents import Incident
from sentinelflow.workflows.access_review.deps import AccessReviewDeps
from sentinelflow.workflows.access_review.nodes import (
    make_list_accounts,
    make_raise_findings,
    make_review,
)
from sentinelflow.workflows.access_review.state import ReviewState

AccessReviewGraph = CompiledStateGraph[ReviewState, None, ReviewState, ReviewState]


@dataclass(frozen=True, slots=True)
class AccessReviewResult:
    """Every finding of the run and the incidents opened for it."""

    findings: tuple[Finding, ...]
    new_incidents: tuple[Incident, ...]

    @property
    def new_incident_ids(self) -> tuple[str, ...]:
        """Ids of the incidents this run opened."""
        return tuple(i.id for i in self.new_incidents)


def build_access_review_graph(deps: AccessReviewDeps) -> AccessReviewGraph:
    """Return the compiled access-review graph."""
    graph = StateGraph(ReviewState)
    graph.add_node("list_accounts", make_list_accounts(deps))
    graph.add_node("review", make_review(deps))
    graph.add_node("raise_findings", make_raise_findings(deps))
    graph.add_edge(START, "list_accounts")
    graph.add_edge("list_accounts", "review")
    graph.add_edge("review", "raise_findings")
    graph.add_edge("raise_findings", END)
    return graph.compile()


def run_access_review(graph: AccessReviewGraph, tenant_id: str) -> AccessReviewResult:
    """Review ``tenant_id``'s accounts."""
    final = cast(ReviewState, graph.invoke({"tenant_id": tenant_id}))
    return AccessReviewResult(final.get("findings", ()), final.get("new_incidents", ()))
