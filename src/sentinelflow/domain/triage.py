"""Outcome of triaging an incident, and how it changes the incident."""

from dataclasses import dataclass, replace

from sentinelflow.domain.incidents import Incident, Verdict
from sentinelflow.domain.lifecycle import IncidentEvent, transition
from sentinelflow.domain.severity import Severity


@dataclass(frozen=True, slots=True)
class TriageResult:
    """Severity (from rules) and verdict (from the LLM, overridden when unsafe)."""

    severity: Severity
    verdict: Verdict
    rationale: str


def apply_triage(incident: Incident, result: TriageResult) -> Incident:
    """Return ``incident`` updated with triage severity, verdict and the next status.

    A false positive closes the incident; anything else marks it triaged.

    Raises:
        InvalidTransitionError: If the incident is not in a status triage can follow.
    """
    event = (
        IncidentEvent.TRIAGE_DISMISSED
        if result.verdict is Verdict.FALSE_POSITIVE
        else IncidentEvent.TRIAGE_CONFIRMED
    )
    moved = transition(incident, event)
    return replace(moved, severity=result.severity, verdict=result.verdict)
