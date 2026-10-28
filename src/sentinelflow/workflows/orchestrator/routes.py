"""Routing between lifecycle steps (pure decisions over repository state)."""

from collections.abc import Callable

from sentinelflow.domain.approvals import ApprovalStatus
from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.workflows.orchestrator._context import load_incident
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.state import LifecycleState
from sentinelflow.workflows.orchestrator.steps.await_step import current_approvals

END = "__end__"
Route = Callable[[LifecycleState], str]


def after_triage(deps: LifecycleDeps) -> Route:
    """Closed (false positive) incidents stop; everything else is investigated."""
    return lambda state: (
        END if load_incident(deps, state).status is IncidentStatus.CLOSED else "investigate"
    )


def after_investigation(state: LifecycleState) -> str:
    """Wait for approvals if any were requested; otherwise report the escalation."""
    return "await_decisions" if state.get("approval_ids") else "report"


def after_await(deps: LifecycleDeps) -> Route:
    """Keep waiting while any approval is pending; then contain."""

    def route(state: LifecycleState) -> str:
        approvals = current_approvals(deps, state)
        waiting = any(a.status is ApprovalStatus.PENDING for a in approvals)
        return "await_decisions" if waiting else "contain"

    return route
