"""Tests for applying a triage result to an incident."""

import pytest

from sentinelflow.domain.errors import InvalidTransitionError
from sentinelflow.domain.incidents import IncidentStatus, Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.domain.triage import TriageResult, apply_triage
from tests.builders import an_incident


@pytest.mark.parametrize(
    ("verdict", "status"),
    [
        (Verdict.TRUE_POSITIVE, IncidentStatus.TRIAGED),
        (Verdict.NEEDS_REVIEW, IncidentStatus.TRIAGED),
        (Verdict.FALSE_POSITIVE, IncidentStatus.CLOSED),
    ],
)
def test_apply_triage_sets_status_severity_and_verdict(
    verdict: Verdict, status: IncidentStatus
) -> None:
    result = TriageResult(severity=Severity.CRITICAL, verdict=verdict, rationale="r")
    updated = apply_triage(an_incident(severity=Severity.LOW), result)
    assert (updated.status, updated.severity, updated.verdict) == (
        status,
        Severity.CRITICAL,
        verdict,
    )


def test_apply_triage_requires_new_incident() -> None:
    result = TriageResult(severity=Severity.LOW, verdict=Verdict.TRUE_POSITIVE, rationale="r")
    with pytest.raises(InvalidTransitionError):
        apply_triage(an_incident(status=IncidentStatus.CLOSED), result)
