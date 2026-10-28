"""Everything a scenario needs to produce deterministic output."""

from dataclasses import dataclass
from random import Random

from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory


@dataclass(frozen=True, slots=True)
class ScenarioContext:
    """Injected sources of randomness, time and ids for one scenario run.

    Note:
        Scenarios must draw every random choice from ``rng`` (never the global
        ``random`` module) so the same seed always reproduces the same output.
    """

    rng: Random
    clock: Clock
    ids: IdFactory
    tenant_id: str
