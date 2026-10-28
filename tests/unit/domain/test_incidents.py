"""Tests for the Incident value object and its enums."""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from sentinelflow.domain.errors import InvalidValueError
from sentinelflow.domain.incidents import IncidentStatus, Verdict
from tests.builders import an_incident


def test_incident_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        an_incident().status = IncidentStatus.CLOSED  # type: ignore[misc]


def test_incident_requires_at_least_one_alert() -> None:
    with pytest.raises(InvalidValueError, match="alert_ids"):
        an_incident(alert_ids=())


def test_naive_created_at_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="created_at"):
        an_incident(created_at=datetime(2026, 1, 1))  # noqa: DTZ001


@pytest.mark.parametrize("field", ["id", "tenant_id", "team"])
def test_blank_identifier_is_rejected(field: str) -> None:
    with pytest.raises(InvalidValueError, match=field):
        an_incident(**{field: ""})


def test_status_and_verdict_values_are_stable_strings() -> None:
    assert IncidentStatus.AWAITING_APPROVAL == "awaiting_approval"
    assert Verdict.FALSE_POSITIVE == "false_positive"
