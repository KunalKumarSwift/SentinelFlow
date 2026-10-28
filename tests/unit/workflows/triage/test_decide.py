"""Tests for the fail-safe verdict decision."""

import pytest

from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.domain.triage import TriageResult
from sentinelflow.workflows.triage.nodes.decide import decide
from sentinelflow.workflows.triage.schema import TriageClassification
from sentinelflow.workflows.triage.state import DecideInput

V = Verdict


def _decide(
    severity: Severity, verdict: V | None, indicators: tuple[str, ...] = ()
) -> TriageResult:
    classification = (
        None if verdict is None else TriageClassification(verdict=verdict, rationale="r")
    )
    state: DecideInput = {
        "severity": severity,
        "classification": classification,
        "injection_indicators": indicators,
    }
    result = decide(state).get("result")
    assert result is not None
    return result


@pytest.mark.parametrize(
    ("severity", "llm_verdict", "expected"),
    [
        (Severity.HIGH, V.TRUE_POSITIVE, V.TRUE_POSITIVE),
        (Severity.LOW, V.FALSE_POSITIVE, V.FALSE_POSITIVE),
        (Severity.MEDIUM, V.NEEDS_REVIEW, V.NEEDS_REVIEW),
        (Severity.HIGH, V.FALSE_POSITIVE, V.NEEDS_REVIEW),
        (Severity.CRITICAL, V.FALSE_POSITIVE, V.NEEDS_REVIEW),
        (Severity.MEDIUM, None, V.NEEDS_REVIEW),
    ],
)
def test_decide(severity: Severity, llm_verdict: V | None, expected: V) -> None:
    result = _decide(severity, llm_verdict)
    assert (result.severity, result.verdict) == (severity, expected)


def test_missing_classification_explains_why() -> None:
    result = _decide(Severity.MEDIUM, None)
    assert "unavailable" in result.rationale


def test_suspected_injection_forces_review_whatever_the_llm_says() -> None:
    result = _decide(Severity.LOW, V.FALSE_POSITIVE, ("verdict_steering",))
    assert result.verdict is V.NEEDS_REVIEW
    assert result.injection_indicators == ("verdict_steering",)
    assert "verdict_steering" in result.rationale
