"""State of the investigation graph; each node declares the keys it reads."""

from typing import NotRequired, Protocol, TypedDict

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.attack import AttackTechnique
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.investigation import InvestigationResult
from sentinelflow.domain.timeline import TimelineEntry
from sentinelflow.workflows.investigation.schema import InvestigationAnalysis


class InvestigationInput(TypedDict):
    """What a caller supplies."""

    incident: Incident
    alert: Alert


class SummarizeInput(InvestigationInput):
    """Inputs plus the related events."""

    events: tuple[SecurityEvent, ...]


class AnalyseInput(InvestigationInput):
    """What the LLM prompt is built from."""

    timeline: tuple[TimelineEntry, ...]
    candidates: tuple[AttackTechnique, ...]


class SelectInput(AnalyseInput):
    """Everything ``select`` validates."""

    analysis: InvestigationAnalysis | None


class InvestigationUpdate(TypedDict, total=False):
    """Partial state a node returns."""

    events: tuple[SecurityEvent, ...]
    timeline: tuple[TimelineEntry, ...]
    candidates: tuple[AttackTechnique, ...]
    analysis: InvestigationAnalysis | None
    result: InvestigationResult


class InvestigationState(InvestigationInput):
    """All channels of the investigation graph."""

    events: NotRequired[tuple[SecurityEvent, ...]]
    timeline: NotRequired[tuple[TimelineEntry, ...]]
    candidates: NotRequired[tuple[AttackTechnique, ...]]
    analysis: NotRequired[InvestigationAnalysis | None]
    result: NotRequired[InvestigationResult]


class Node[In](Protocol):
    """An investigation node."""

    def __call__(self, state: In) -> InvestigationUpdate:
        """Run the node."""
        ...
