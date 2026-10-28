"""Queue workflow runs on behalf of an authenticated principal."""

from sentinelflow.api.container import ApiContainer
from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.domain.errors import InvalidTransitionError
from sentinelflow.domain.incidents import Incident, IncidentStatus
from sentinelflow.domain.principals import Principal


def enqueue_triage(container: ApiContainer, principal: Principal, incident: Incident) -> str:
    """Queue a triage run for ``incident`` and return its run id.

    Raises:
        InvalidTransitionError: If the incident is no longer ``NEW`` (triage would fail).
    """
    if incident.status is not IncidentStatus.NEW:
        raise InvalidTransitionError(f"incident {incident.id} is {incident.status}, not new")
    run_id = container.ids.new_id("run")
    command = StartRun(
        run_id=run_id,
        tenant_id=principal.tenant_id,
        workflow="triage",
        incident_id=incident.id,
        alert_id=incident.alert_ids[0],
        initiator=principal.subject,
    )
    container.queue.publish(command)
    details = {"run_id": run_id, "workflow": "triage"}
    container.recorder().record(principal, "run.queued", incident.id, details)
    return run_id
