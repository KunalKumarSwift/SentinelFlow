"""Seed data for mock providers that matches what ``sentinelflow-sim`` will send.

Each scenario draws its users and IPs from ``Random(seed)`` before anything else, so
running every scenario with the same seed here reproduces the simulator's entities.
"""

from random import Random

from sentinelflow.core.clock import SystemClock
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.output import SeedData
from sentinelflow.simulator.registry import SCENARIOS


def demo_seed_data(seed: int) -> SeedData:
    """Return the union of every scenario's seed data for ``seed``."""
    outputs = [
        scenario(ScenarioContext(Random(seed), SystemClock(), UuidIdFactory(), "demo"))
        for scenario in SCENARIOS.values()
    ]
    return SeedData(
        users=tuple(u for out in outputs for u in out.seed_data.users),
        ip_reputations=tuple(r for out in outputs for r in out.seed_data.ip_reputations),
    )
