"""Await step: pause the run (LangGraph ``interrupt``) until every approval is decided.

The resume payload is only a wake-up call; decisions are always re-read from the
approval repository, so a forged or stale resume cannot approve anything.
"""

from langgraph.types import interrupt

from sentinelflow.domain.approvals import Approval, ApprovalStatus, expire_if_due
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.state import LifecycleState, LifecycleUpdate, Step


def make_await_step(deps: LifecycleDeps) -> Step:
    """Build the step that waits for human decisions."""

    def await_decisions(state: LifecycleState) -> LifecycleUpdate:
        pending = [
            a.id for a in current_approvals(deps, state) if a.status is ApprovalStatus.PENDING
        ]
        if pending:
            interrupt({"run_id": state["run_id"], "pending_approvals": pending})
        return {}

    return await_decisions


def current_approvals(deps: LifecycleDeps, state: LifecycleState) -> list[Approval]:
    """Load the run's approvals, expiring any that are past due."""
    ids, tenant = state.get("approval_ids", []), state["tenant_id"]
    stored = [a for i in ids if (a := deps.approvals.get(tenant, i)) is not None]
    current = [expire_if_due(a, deps.clock.now()) for a in stored]
    for before, after in zip(stored, current, strict=True):
        if after is not before:
            deps.approvals.update(after)
    return current
