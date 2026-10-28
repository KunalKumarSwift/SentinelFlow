"""The server's demo seed matches what the simulator generates for the same seed."""

from sentinelflow.simulator.demo_seed import demo_seed_data
from sentinelflow.simulator.registry import SCENARIOS
from tests.unit.simulator.conftest import make_context


def test_seed_contains_every_scenarios_users_and_intel() -> None:
    seed = demo_seed_data(7)
    for name in SCENARIOS:
        out = SCENARIOS[name](make_context(7))
        assert set(out.seed_data.users) <= set(seed.users)
        assert set(out.seed_data.ip_reputations) <= set(seed.ip_reputations)
