"""Investigation step: investigate, then request approval for each proposed action.

Each proposal goes through the tool guard as ``action:propose`` on behalf of the run's
initiator; a denied proposal simply produces no approval (and a ``tool.denied`` record).
"""

from sentinelflow.domain.actions import ProposedAction
from sentinelflow.domain.approvals import new_approval
from sentinelflow.domain.errors import PolicyDeniedError
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.lifecycle import IncidentEvent, transition
from sentinelflow.security.permissions import Permission
from sentinelflow.security.tool_guard import ToolCall
from sentinelflow.workflows.investigation import run_investigation
from sentinelflow.workflows.orchestrator._context import (
    load_alert,
    load_incident,
    resource_of,
    run_context,
    save,
)
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.notify import notify_approvers
from sentinelflow.workflows.orchestrator.state import LifecycleState, LifecycleUpdate, Step


def make_investigate_step(deps: LifecycleDeps) -> Step:
    """Build the investigation step."""

    def investigate(state: LifecycleState) -> LifecycleUpdate:
        incident = transition(load_incident(deps, state), IncidentEvent.INVESTIGATION_STARTED)
        result = run_investigation(deps.investigation, incident, load_alert(deps, state))
        approval_ids = [i for a in result.actions if (i := _propose(deps, state, incident, a))]
        event = IncidentEvent.ACTIONS_PROPOSED if approval_ids else IncidentEvent.NO_SAFE_ACTION
        details = {
            "run_id": state["run_id"],
            "techniques": ",".join(t.technique_id for t in result.techniques),
            "approvals": ",".join(approval_ids),
            "dropped": ",".join(result.dropped),
        }
        investigated = transition(incident, event)
        save(deps, investigated, "incident.investigated", details)
        notify_approvers(deps, investigated, approval_ids)
        return {"approval_ids": approval_ids}

    return investigate


def _propose(
    deps: LifecycleDeps, state: LifecycleState, incident: Incident, action: ProposedAction
) -> str | None:
    call = ToolCall(f"propose:{action.id}", Permission.ACTION_PROPOSE, resource_of(incident))
    approval = new_approval(
        deps.ids.new_id("apr"),
        incident.tenant_id,
        state["run_id"],
        action,
        incident.severity,
        deps.clock.now(),
    )
    try:
        deps.guard.run(call, run_context(deps, state), lambda _: deps.approvals.add(approval))
    except PolicyDeniedError:
        return None
    return approval.id
