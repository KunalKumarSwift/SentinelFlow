"""Queue workflow runs and record who they run on behalf of."""

from sentinelflow.api.container import ApiContainer
from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.domain.errors import InvalidTransitionError
from sentinelflow.domain.incidents import Incident, IncidentStatus
from sentinelflow.domain.principals import Principal
from sentinelflow.domain.runs import RunRecord, RunStatus


def enqueue_triage(
    container: ApiContainer,
    actor: Principal,
    incident: Incident,
    initiator: Principal | None = None,
) -> str:
    """Create a run record, queue the incident lifecycle and return the run id.

    Args:
        container: API services.
        actor: Who made the request (audited).
        incident: The incident to process; must still be ``NEW``.
        initiator: Whose authority the run carries; defaults to ``actor``. Alert-triggered
            runs pass the orchestrator, because alert sources may not propose actions.

    Raises:
        InvalidTransitionError: If the incident is no longer ``NEW`` (triage would fail).
    """
    if incident.status is not IncidentStatus.NEW:
        raise InvalidTransitionError(f"incident {incident.id} is {incident.status}, not new")
    owner, run_id = initiator or actor, container.ids.new_id("run")
    alert_id, now = incident.alert_ids[0], container.clock.now()
    record = RunRecord(
        run_id, actor.tenant_id, "triage", incident.id, alert_id, owner, RunStatus.QUEUED, now
    )
    container.runs.add(record)
    container.queue.publish(
        StartRun(run_id, actor.tenant_id, "triage", incident.id, alert_id, owner.subject)
    )
    details = {"run_id": run_id, "workflow": "triage", "initiator": owner.subject}
    container.recorder().record(actor, "run.queued", incident.id, details)
    return run_id
