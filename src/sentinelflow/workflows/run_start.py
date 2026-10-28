"""Queue an incident-lifecycle run: record it, publish ``StartRun``, audit ``run.queued``.

Shared by the API (alerts and manual starts) and scheduled jobs (access review).
"""

from dataclasses import dataclass

from sentinelflow.contracts.run_queue import RunQueue, StartRun
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory
from sentinelflow.domain.errors import InvalidTransitionError
from sentinelflow.domain.incidents import Incident, IncidentStatus
from sentinelflow.domain.principals import Principal
from sentinelflow.domain.runs import RunRecord, RunStatus
from sentinelflow.security.audit_recorder import AuditRecorder


@dataclass(frozen=True, slots=True)
class RunStartDeps:
    """Where run records, commands and audit events go."""

    runs: RunRepository
    queue: RunQueue
    ids: IdFactory
    clock: Clock
    recorder: AuditRecorder


def queue_lifecycle_run(
    deps: RunStartDeps, actor: Principal, incident: Incident, initiator: Principal | None = None
) -> str:
    """Create a run record, queue the incident lifecycle and return the run id.

    Args:
        deps: Run storage, queue, ids, clock and audit.
        actor: Who made the request (audited).
        incident: The incident to process; must still be ``NEW``.
        initiator: Whose authority the run carries; defaults to ``actor``. Alert-triggered
            runs pass the orchestrator, because alert sources may not propose actions.

    Raises:
        InvalidTransitionError: If the incident is no longer ``NEW`` (triage would fail).
    """
    if incident.status is not IncidentStatus.NEW:
        raise InvalidTransitionError(f"incident {incident.id} is {incident.status}, not new")
    owner, run_id = initiator or actor, deps.ids.new_id("run")
    alert_id, now = incident.alert_ids[0], deps.clock.now()
    record = RunRecord(
        run_id, actor.tenant_id, "triage", incident.id, alert_id, owner, RunStatus.QUEUED, now
    )
    deps.runs.add(record)
    deps.queue.publish(
        StartRun(run_id, actor.tenant_id, "triage", incident.id, alert_id, owner.subject)
    )
    details = {"run_id": run_id, "workflow": "triage", "initiator": owner.subject}
    deps.recorder.record(actor, "run.queued", incident.id, details)
    return run_id
