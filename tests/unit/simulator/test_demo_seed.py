"""The server's demo seed matches what the simulator generates for the same seed."""

from sentinelflow.simulator.demo_seed import DEMO_TENANT, demo_events, demo_seed_data
from sentinelflow.simulator.registry import SCENARIOS
from tests.unit.simulator.conftest import make_context


def test_seed_contains_every_scenarios_users_and_intel() -> None:
    seed = demo_seed_data(7)
    for name in SCENARIOS:
        out = SCENARIOS[name](make_context(7))
        assert set(out.seed_data.users) <= set(seed.users)
        assert set(out.seed_data.ip_reputations) <= set(seed.ip_reputations)


def test_demo_events_belong_to_demo_tenant_and_cover_each_scenario() -> None:
    events = demo_events(7)
    assert {e.tenant_id for e in events} == {DEMO_TENANT}
    assert {"login_failed", "login_succeeded"} <= {e.kind for e in events}
