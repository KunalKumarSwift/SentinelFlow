"""Tests for the brute-force scenario."""

from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.scenarios.brute_force import generate
from tests.unit.simulator.conftest import make_context


def test_raises_one_brute_force_alert() -> None:
    out = generate(make_context())
    assert [a.rule_id for a in out.alerts] == ["brute_force_success"]


def test_many_failures_then_one_success_from_one_ip() -> None:
    events = generate(make_context()).events
    kinds = [e.kind for e in events]
    assert 30 <= kinds.count("login_failed") <= 60
    assert kinds[-1] == "login_succeeded"
    assert len({e.entities.ip for e in events}) == 1


def test_events_are_in_time_order_before_the_alert() -> None:
    out = generate(make_context())
    times = [e.at for e in out.events]
    assert times == sorted(times)
    assert times[-1] <= out.alerts[0].observed_at


def test_attacker_ip_is_known_malicious() -> None:
    out = generate(make_context())
    rep = out.seed_data.enrichment_for(out.alerts[0].entities).ip_reputation
    assert rep is not None and rep.is_malicious


def test_expected_outcome_is_high_true_positive() -> None:
    expected = generate(make_context()).expected
    assert (expected.severity, expected.verdict) == (Severity.HIGH, Verdict.TRUE_POSITIVE)
