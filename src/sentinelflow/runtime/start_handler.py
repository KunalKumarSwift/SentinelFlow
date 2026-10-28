"""Handle ``StartRun``: load the incident and alert, run the lifecycle, save the result."""

from sentinelflow.contracts.repositories import AlertRepository, IncidentRepository
from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.system_principals import orchestrator_for
from sentinelflow.workflows.orchestrator import run_lifecycle
from sentinelflow.workflows.orchestrator.graph import LifecycleGraph


class StartRunHandler:
    """Runs the incident lifecycle for a queued command."""

    def __init__(
        self,
        alerts: AlertRepository,
        incidents: IncidentRepository,
        graph: LifecycleGraph,
        recorder: AuditRecorder,
    ) -> None:
        """Wire the repositories, the compiled lifecycle graph and the audit recorder."""
        self._alerts, self._incidents, self._graph = alerts, incidents, graph
        self._recorder = recorder

    def __call__(self, command: StartRun) -> None:
        """Run the lifecycle and persist the updated incident.

        Raises:
            NotFoundError: If the incident or alert no longer exists (not retryable).
        """
        incident = self._incidents.get(command.tenant_id, command.incident_id)
        if incident is None:
            raise NotFoundError(f"incident {command.incident_id} not found")
        stored = self._alerts.get(command.tenant_id, command.alert_id)
        if stored is None:
            raise NotFoundError(f"alert {command.alert_id} not found")
        updated = run_lifecycle(self._graph, incident, stored.alert)
        self._incidents.update(updated)
        details = {
            "run_id": command.run_id,
            "status": updated.status.value,
            "severity": str(updated.severity),
            "verdict": "" if updated.verdict is None else updated.verdict.value,
        }
        actor = orchestrator_for(command.tenant_id)
        self._recorder.record(actor, "incident.triaged", updated.id, details)
