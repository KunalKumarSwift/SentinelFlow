"""Tests for the prompt-injection scenario."""

from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.security.injection import detect_injection
from sentinelflow.simulator.scenarios.prompt_injection import generate
from tests.unit.simulator.conftest import make_context


def test_alert_carries_injection_text_in_raw_fields() -> None:
    alert = generate(make_context()).alerts[0]
    assert alert.rule_id == "brute_force_success"
    assert detect_injection(alert.raw.values())


def test_expected_outcome_is_high_needs_review() -> None:
    expected = generate(make_context()).expected
    assert (expected.severity, expected.verdict) == (Severity.HIGH, Verdict.NEEDS_REVIEW)
