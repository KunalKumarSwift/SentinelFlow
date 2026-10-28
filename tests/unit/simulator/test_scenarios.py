"""Properties every registered scenario must satisfy."""

import pytest

from sentinelflow.domain.scoring import score_severity
from sentinelflow.simulator.registry import SCENARIOS
from tests.unit.simulator.conftest import make_context


def test_registry_lists_phase_one_scenarios() -> None:
    assert {"brute_force", "benign_travel"} <= set(SCENARIOS)


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_same_seed_gives_identical_output(name: str) -> None:
    assert SCENARIOS[name](make_context(7)) == SCENARIOS[name](make_context(7))


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_different_seeds_give_different_output(name: str) -> None:
    assert SCENARIOS[name](make_context(1)) != SCENARIOS[name](make_context(2))


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_seed_data_scores_to_expected_severity(name: str) -> None:
    out = SCENARIOS[name](make_context())
    alert = out.alerts[0]
    enrichment = out.seed_data.enrichment_for(alert.entities)
    assert score_severity(alert.rule_id, alert.entities, enrichment) is out.expected.severity


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_alerts_and_events_belong_to_context_tenant(name: str) -> None:
    out = SCENARIOS[name](make_context())
    assert {a.tenant_id for a in out.alerts} | {e.tenant_id for e in out.events} == {"acme"}
