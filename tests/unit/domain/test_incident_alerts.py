"""Tests for attaching alerts to incidents."""

from sentinelflow.domain.incidents import with_alert
from tests.builders import an_incident


def test_with_alert_appends_alert_id() -> None:
    assert with_alert(an_incident(), "alt-0002").alert_ids == ("alt-0001", "alt-0002")


def test_with_alert_ignores_alert_already_attached() -> None:
    assert with_alert(an_incident(), "alt-0001").alert_ids == ("alt-0001",)
