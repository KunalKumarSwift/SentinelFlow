"""Tests for the benign impossible-travel scenario (VPN egress)."""

from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.scenarios.benign_travel import generate
from tests.unit.simulator.conftest import make_context


def test_raises_impossible_travel_from_internal_vpn_ip() -> None:
    alert = generate(make_context()).alerts[0]
    assert alert.rule_id == "impossible_travel"
    assert alert.entities.ip is not None and alert.entities.ip.startswith("10.")


def test_has_two_logins_from_different_countries() -> None:
    events = generate(make_context()).events
    assert [e.kind for e in events] == ["login_succeeded", "login_succeeded"]
    assert events[0].attributes["country"] != events[1].attributes["country"]


def test_expected_outcome_is_low_false_positive() -> None:
    expected = generate(make_context()).expected
    assert (expected.severity, expected.verdict) == (Severity.LOW, Verdict.FALSE_POSITIVE)
