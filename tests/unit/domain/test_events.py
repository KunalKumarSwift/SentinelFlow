"""Tests for raw security events."""

from datetime import datetime

import pytest

from sentinelflow.domain.errors import InvalidValueError
from sentinelflow.domain.events import SecurityEvent
from tests.builders import T0, some_entities


def _event(**changes: object) -> SecurityEvent:
    fields: dict[str, object] = {
        "id": "evt-0001",
        "tenant_id": "acme",
        "at": T0,
        "kind": "login_failed",
        "entities": some_entities(),
        "attributes": {"user_agent": "curl/8"},
    }
    return SecurityEvent(**fields | changes)  # type: ignore[arg-type]


def test_attributes_are_read_only_copies() -> None:
    attributes = {"user_agent": "curl/8"}
    event = _event(attributes=attributes)
    attributes["user_agent"] = "changed"
    assert event.attributes["user_agent"] == "curl/8"
    with pytest.raises(TypeError):
        event.attributes["x"] = "y"  # type: ignore[index]


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="at"):
        _event(at=datetime(2026, 1, 1))  # noqa: DTZ001


def test_blank_kind_is_rejected() -> None:
    with pytest.raises(InvalidValueError, match="kind"):
        _event(kind="")
