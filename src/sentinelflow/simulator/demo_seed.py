"""Seed data for mock providers that matches what ``sentinelflow-sim`` will send.

Each scenario draws its users and IPs from ``Random(seed)`` before anything else, so
running every scenario with the same seed here reproduces the simulator's entities.
"""

from random import Random

from sentinelflow.core.clock import SystemClock
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.output import ScenarioOutput, SeedData
from sentinelflow.simulator.registry import SCENARIOS

DEMO_TENANT = "acme"


def demo_seed_data(seed: int) -> SeedData:
    """Return the union of every scenario's seed data for ``seed``."""
    outputs = _outputs(seed)
    return SeedData(
        users=tuple(u for out in outputs for u in out.seed_data.users),
        ip_reputations=tuple(r for out in outputs for r in out.seed_data.ip_reputations),
    )


def demo_events(seed: int) -> tuple[SecurityEvent, ...]:
    """Return every scenario's raw events for the demo tenant (for the event store)."""
    return tuple(e for out in _outputs(seed) for e in out.events)


def _outputs(seed: int) -> list[ScenarioOutput]:
    return [
        scenario(ScenarioContext(Random(seed), SystemClock(), UuidIdFactory(), DEMO_TENANT))
        for scenario in SCENARIOS.values()
    ]
