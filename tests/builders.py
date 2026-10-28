"""Test-data builders: valid domain objects with overridable fields.

Each test states only the fields it cares about, e.g. ``an_alert(rule_id="x")``.
"""

from dataclasses import replace
from datetime import UTC, datetime

from sentinelflow.domain.alerts import Alert, Entities
from sentinelflow.domain.incidents import Incident, IncidentStatus
from sentinelflow.domain.severity import Severity

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)


def some_entities(**changes: str | None) -> Entities:
    """Return entities for a user logging in from an external IP."""
    return replace(Entities(user="alice", ip="203.0.113.9"), **changes)


def an_alert(**changes: object) -> Alert:
    """Return a valid brute-force alert for tenant ``acme``."""
    alert = Alert(
        id="alt-0001",
        tenant_id="acme",
        source="simulator",
        rule_id="brute_force_success",
        title="Successful login after repeated failures",
        observed_at=T0,
        entities=some_entities(),
        raw={"failed_attempts": "42"},
    )
    return replace(alert, **changes)  # pyright: ignore[reportArgumentType] -- test overrides


def an_incident(**changes: object) -> Incident:
    """Return a valid new incident for tenant ``acme``, team ``soc-emea``."""
    incident = Incident(
        id="inc-0001",
        tenant_id="acme",
        team="soc-emea",
        status=IncidentStatus.NEW,
        severity=Severity.HIGH,
        verdict=None,
        alert_ids=("alt-0001",),
        entities=some_entities(),
        created_at=T0,
    )
    return replace(incident, **changes)  # pyright: ignore[reportArgumentType] -- test overrides
