"""Shared fixtures: a deterministic scenario context."""

from random import Random

from sentinelflow.simulator.context import ScenarioContext
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_ids import SequentialIdFactory


def make_context(seed: int = 42) -> ScenarioContext:
    """Return a fresh context; equal seeds give identical scenario output."""
    return ScenarioContext(
        rng=Random(seed), clock=FakeClock(T0), ids=SequentialIdFactory(), tenant_id="acme"
    )
