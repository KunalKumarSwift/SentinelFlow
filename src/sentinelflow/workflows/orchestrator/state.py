"""State of the incident lifecycle graph (Phase 1: triage only)."""

from typing import NotRequired, TypedDict

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.triage import TriageResult


class LifecycleInput(TypedDict):
    """What starts a lifecycle run."""

    incident: Incident
    alert: Alert


class TriagedInput(TypedDict):
    """What ``apply_triage_result`` reads."""

    incident: Incident
    triage: TriageResult


class LifecycleUpdate(TypedDict, total=False):
    """Partial state a lifecycle node returns."""

    incident: Incident
    triage: TriageResult


class LifecycleState(TypedDict):
    """All channels of the lifecycle graph."""

    incident: Incident
    alert: Alert
    triage: NotRequired[TriageResult]
