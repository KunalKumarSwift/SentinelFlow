"""Queue workflow runs from the API (delegates to ``workflows/run_start``)."""

from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.principals import Principal
from sentinelflow.workflows.run_start import RunStartDeps, queue_lifecycle_run


def enqueue_triage(
    container: ApiContainer,
    actor: Principal,
    incident: Incident,
    initiator: Principal | None = None,
) -> str:
    """Queue the incident lifecycle; see ``queue_lifecycle_run`` for the rules."""
    deps = RunStartDeps(
        container.runs, container.queue, container.ids, container.clock, container.recorder()
    )
    return queue_lifecycle_run(deps, actor, incident, initiator)
