"""Dependencies the investigation graph needs from the outside world."""

from dataclasses import dataclass

from sentinelflow.contracts.event_store import EventStore
from sentinelflow.contracts.llm import LLMProvider


@dataclass(frozen=True, slots=True)
class InvestigationDeps:
    """Injected collaborators; built once in the composition root."""

    events: EventStore
    llm: LLMProvider
