"""Dependencies the triage graph needs from the outside world."""

from dataclasses import dataclass

from sentinelflow.contracts.identity import IdentityProvider
from sentinelflow.contracts.llm import LLMProvider
from sentinelflow.contracts.threat_intel import ThreatIntelProvider


@dataclass(frozen=True, slots=True)
class TriageDeps:
    """Injected collaborators; built once in the composition root."""

    intel: ThreatIntelProvider
    identity: IdentityProvider
    llm: LLMProvider
