"""Tests for the Alert and Entities value objects."""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from sentinelflow.domain.errors import InvalidValueError
from tests.builders import an_alert, some_entities


def test_alert_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        an_alert().title = "changed"  # type: ignore[misc]


def test_raw_fields_cannot_be_mutated() -> None:
    with pytest.raises(TypeError):
        an_alert().raw["failed_attempts"] = "0"  # type: ignore[index]


def test_raw_fields_are_copied_from_caller_dict() -> None:
    raw = {"failed_attempts": "42"}
    alert = an_alert(raw=raw)
    raw["failed_attempts"] = "0"
    assert alert.raw["failed_attempts"] == "42"


def test_alerts_with_same_fields_are_equal_and_hashable() -> None:
    assert an_alert() == an_alert()
    assert len({an_alert(), an_alert()}) == 1


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="observed_at"):
        an_alert(observed_at=datetime(2026, 1, 1))  # noqa: DTZ001


@pytest.mark.parametrize("field", ["id", "tenant_id", "rule_id"])
def test_blank_identifier_is_rejected(field: str) -> None:
    with pytest.raises(InvalidValueError, match=field):
        an_alert(**{field: " "})


def test_entities_lists_only_present_values() -> None:
    entities = some_entities(host="ws-17")
    assert entities.present() == {"user": "alice", "ip": "203.0.113.9", "host": "ws-17"}
