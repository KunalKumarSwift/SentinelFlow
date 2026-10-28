"""Shared load/save helpers for lifecycle steps."""

from collections.abc import Mapping

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.incidents import Incident
from sentinelflow.security.policy import Resource
from sentinelflow.security.system_principals import orchestrator_for
from sentinelflow.security.tool_guard import RunContext
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.state import LifecycleState


def load_incident(deps: LifecycleDeps, state: LifecycleState) -> Incident:
    """Return the run's incident or raise ``NotFoundError``."""
    incident = deps.incidents.get(state["tenant_id"], state["incident_id"])
    if incident is None:
        raise NotFoundError(f"incident {state['incident_id']} not found")
    return incident


def load_alert(deps: LifecycleDeps, state: LifecycleState) -> Alert:
    """Return the run's alert or raise ``NotFoundError``."""
    stored = deps.alerts.get(state["tenant_id"], state["alert_id"])
    if stored is None:
        raise NotFoundError(f"alert {state['alert_id']} not found")
    return stored.alert


def run_context(deps: LifecycleDeps, state: LifecycleState) -> RunContext:
    """Return the tool-guard context: the run's initiator and the containment scope."""
    record = deps.runs.get(state["tenant_id"], state["run_id"])
    if record is None:
        raise NotFoundError(f"run {state['run_id']} not found")
    return RunContext(record.id, record.initiator, deps.containment_scope)


def resource_of(incident: Incident) -> Resource:
    """Return the policy resource for an incident."""
    return Resource("incident", incident.id, incident.tenant_id, incident.team)


def save(deps: LifecycleDeps, incident: Incident, verb: str, details: Mapping[str, str]) -> None:
    """Persist ``incident`` and audit the change as the orchestrator."""
    deps.incidents.update(incident)
    deps.recorder.record(orchestrator_for(incident.tenant_id), verb, incident.id, details)
