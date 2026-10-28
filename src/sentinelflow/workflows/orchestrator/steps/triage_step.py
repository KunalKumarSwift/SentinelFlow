"""Triage step: run the triage sub-workflow and apply its result to the incident."""

from sentinelflow.domain.triage import apply_triage
from sentinelflow.workflows.orchestrator._context import load_alert, load_incident, save
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps
from sentinelflow.workflows.orchestrator.state import LifecycleState, LifecycleUpdate, Step
from sentinelflow.workflows.triage import run_triage


def make_triage_step(deps: LifecycleDeps) -> Step:
    """Build the triage step."""

    def triage(state: LifecycleState) -> LifecycleUpdate:
        incident = load_incident(deps, state)
        result = run_triage(deps.triage, incident, load_alert(deps, state))
        updated = apply_triage(incident, result)
        details = {
            "run_id": state["run_id"],
            "severity": str(result.severity),
            "verdict": result.verdict.value,
            "injection": ",".join(result.injection_indicators),
        }
        save(deps, updated, "incident.triaged", details)
        return {}

    return triage
