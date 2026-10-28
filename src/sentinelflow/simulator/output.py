"""What a scenario produces: alerts, raw events, seed data and the expected outcome."""

from dataclasses import dataclass

from sentinelflow.domain.alerts import Alert, Entities
from sentinelflow.domain.enrichment import Enrichment, IpReputation, UserContext
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity


@dataclass(frozen=True, slots=True)
class SeedData:
    """Directory and threat-intel facts that mock providers serve for a scenario."""

    users: tuple[UserContext, ...] = ()
    ip_reputations: tuple[IpReputation, ...] = ()

    def enrichment_for(self, entities: Entities) -> Enrichment:
        """Return the enrichment a triage run should find for ``entities``."""
        user = next((u for u in self.users if u.user_id == entities.user), None)
        rep = next((r for r in self.ip_reputations if r.ip == entities.ip), None)
        return Enrichment(ip_reputation=rep, user=user)


@dataclass(frozen=True, slots=True)
class Expectation:
    """The outcome the platform should reach; makes each scenario a test case."""

    severity: Severity
    verdict: Verdict


@dataclass(frozen=True, slots=True)
class ScenarioOutput:
    """Complete, self-consistent result of one scenario run."""

    name: str
    alerts: tuple[Alert, ...]
    events: tuple[SecurityEvent, ...]
    seed_data: SeedData
    expected: Expectation
