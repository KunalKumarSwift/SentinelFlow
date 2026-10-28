"""Containment step: execute approved actions through the tool guard, then close out."""

from sentinelflow.domain.actions import targets_user
from sentinelflow.domain.approvals import Approval, ApprovalStatus
from sentinelflow.domain.lifecycle import IncidentEvent, transition
from sentinelflow.security.permissions import Permission
from sentinelflow.security.policy import ActionContext
from sentinelflow.security.tool_guard import ToolCall
from sentinelflow.workflows.orchestrator._context import (
    load_incident,
    resource_of,
    run_context,
    save,
)
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.state import LifecycleState, LifecycleUpdate, Step
from sentinelflow.workflows.orchestrator.steps.await_step import current_approvals


def make_contain_step(deps: LifecycleDeps) -> Step:
    """Build the containment step."""

    def contain(state: LifecycleState) -> LifecycleUpdate:
        incident = load_incident(deps, state)
        approved = [
            a for a in current_approvals(deps, state) if a.status is ApprovalStatus.APPROVED
        ]
        executed = [_execute(deps, state, a) for a in approved]
        details = {"run_id": state["run_id"], "executed": ",".join(executed)}
        if not executed:
            escalated = transition(incident, IncidentEvent.APPROVAL_REJECTED)
            save(deps, escalated, "incident.escalated", details)
            return {}
        containing = transition(incident, IncidentEvent.APPROVALS_GRANTED)
        save(
            deps,
            transition(containing, IncidentEvent.CONTAINMENT_DONE),
            "incident.contained",
            details,
        )
        return {}

    return contain


def _execute(deps: LifecycleDeps, state: LifecycleState, approval: Approval) -> str:
    action = approval.action
    incident = load_incident(deps, state)
    target_user = action.target if targets_user(action.kind) else None
    context = ActionContext(target_user=target_user, quorum_met=True)
    call = ToolCall(
        f"execute:{action.id}", Permission.ACTION_EXECUTE, resource_of(incident), context
    )
    result = deps.guard.run(
        call, run_context(deps, state), lambda key: deps.identity.apply(action, key)
    )
    return result.action_id
