"""Builders for triage dependencies with sensible fakes."""

from sentinelflow.contracts.identity import IdentityProvider
from sentinelflow.contracts.llm import LLMProvider
from sentinelflow.contracts.threat_intel import ThreatIntelProvider
from sentinelflow.workflows.triage import TriageDeps
from tests.fakes.fake_identity import FakeIdentityProvider
from tests.fakes.fake_intel import FakeThreatIntel
from tests.fakes.fake_llm import FakeLLM

TP = {"verdict": "true_positive", "rationale": "Repeated failures then success."}
FP = {"verdict": "false_positive", "rationale": "Known VPN egress."}


def deps_with(
    intel: ThreatIntelProvider | None = None,
    identity: IdentityProvider | None = None,
    llm: LLMProvider | None = None,
) -> TriageDeps:
    """Return triage deps, defaulting each collaborator to an empty fake."""
    return TriageDeps(
        intel=intel or FakeThreatIntel([]),
        identity=identity or FakeIdentityProvider([]),
        llm=llm or FakeLLM({"triage.classify": TP}),
    )
