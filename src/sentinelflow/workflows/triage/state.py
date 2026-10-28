"""State that flows through the triage graph.

Each node declares the narrow input it reads (all keys required, so access is
type-safe) and returns a partial ``TriageUpdate``. ``TriageState`` is the union of
all keys and serves only as the graph's channel definition.
"""

from typing import Protocol, TypedDict

from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.enrichment import IpReputation, UserContext
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.severity import Severity
from sentinelflow.domain.triage import TriageResult
from sentinelflow.workflows.triage.schema import TriageClassification


class TriageInput(TypedDict):
    """What a caller supplies to start triage."""

    incident: Incident
    alert: Alert


class ScoreInput(TriageInput):
    """Inputs plus enrichment, as read by ``score``."""

    ip_reputation: IpReputation | None
    user: UserContext | None


class ClassifyInput(ScoreInput):
    """Everything ``classify`` puts in the prompt."""

    severity: Severity


class DecideInput(TypedDict):
    """What ``decide`` combines into the final result."""

    severity: Severity
    classification: TriageClassification | None
    injection_indicators: tuple[str, ...]


class TriageUpdate(TypedDict, total=False):
    """Partial state a node returns."""

    injection_indicators: tuple[str, ...]
    ip_reputation: IpReputation | None
    user: UserContext | None
    severity: Severity
    classification: TriageClassification | None
    result: TriageResult


class TriageState(TriageInput, TriageUpdate):
    """All channels of the triage graph."""


class Node[In](Protocol):
    """A triage node: reads its declared input, returns a partial update."""

    def __call__(self, state: In) -> TriageUpdate:
        """Run the node."""
        ...
