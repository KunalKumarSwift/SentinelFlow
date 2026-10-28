"""Report step: write the post-incident report as a ticket; contained incidents close."""

from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.domain.lifecycle import IncidentEvent, transition
from sentinelflow.security.audit_reader import read_all
from sentinelflow.workflows.orchestrator._context import load_incident, save
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.state import LifecycleState, LifecycleUpdate, Step
from sentinelflow.workflows.report import collect_facts, write_report


def make_report_step(deps: LifecycleDeps) -> Step:
    """Build the reporting step."""

    def report(state: LifecycleState) -> LifecycleUpdate:
        incident = load_incident(deps, state)
        approvals = deps.approvals.for_run(incident.tenant_id, state["run_id"])
        events = read_all(deps.audit, incident.tenant_id)
        facts = collect_facts(incident, approvals, events, deps.redactor)
        body = write_report(deps.llm, facts, incident.tenant_id)
        title = f"[{incident.severity}] {incident.id} {incident.status.value}"
        ticket = deps.ticketing.upsert(incident.tenant_id, incident.id, title, body)
        if incident.status is IncidentStatus.CONTAINED:
            incident = transition(incident, IncidentEvent.REPORT_WRITTEN)
        save(deps, incident, "incident.reported", {"run_id": state["run_id"], "ticket": ticket})
        return {}

    return report
