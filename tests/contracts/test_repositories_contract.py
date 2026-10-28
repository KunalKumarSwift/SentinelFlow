"""Contracts for alert and incident repositories (memory now, Postgres in Phase 2)."""

from collections.abc import Callable

import pytest

from sentinelflow.contracts.repositories import AlertRepository, IncidentRepository, StoredAlert
from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from tests.builders import T0, an_alert, an_incident

ALERT_REPOS: list[Callable[[], AlertRepository]] = [MemoryAlertRepository]
INCIDENT_REPOS: list[Callable[[], IncidentRepository]] = [MemoryIncidentRepository]


@pytest.fixture(params=ALERT_REPOS)
def alerts(request: pytest.FixtureRequest) -> AlertRepository:
    return request.param()


@pytest.fixture(params=INCIDENT_REPOS)
def incidents(request: pytest.FixtureRequest) -> IncidentRepository:
    return request.param()


def test_latest_alert_with_fingerprint_is_returned(alerts: AlertRepository) -> None:
    first = StoredAlert(an_alert(id="alt-1"), "fp", "inc-1")
    second = StoredAlert(an_alert(id="alt-2", observed_at=T0.replace(hour=10)), "fp", "inc-1")
    alerts.add(first)
    alerts.add(second)
    assert alerts.latest_with_fingerprint("acme", "fp") == second


def test_fingerprints_are_isolated_per_tenant(alerts: AlertRepository) -> None:
    alerts.add(StoredAlert(an_alert(tenant_id="globex"), "fp", "inc-1"))
    assert alerts.latest_with_fingerprint("acme", "fp") is None


def test_incident_round_trip_and_update(incidents: IncidentRepository) -> None:
    incidents.add(an_incident())
    incidents.update(an_incident(status=IncidentStatus.TRIAGED))
    stored = incidents.get("acme", "inc-0001")
    assert stored is not None and stored.status is IncidentStatus.TRIAGED


def test_incident_from_other_tenant_is_invisible(incidents: IncidentRepository) -> None:
    incidents.add(an_incident())
    assert incidents.get("globex", "inc-0001") is None


def test_adding_existing_incident_id_is_rejected(incidents: IncidentRepository) -> None:
    incidents.add(an_incident())
    with pytest.raises(ValueError, match="exists"):
        incidents.add(an_incident())


def test_updating_unknown_incident_is_rejected(incidents: IncidentRepository) -> None:
    with pytest.raises(KeyError):
        incidents.update(an_incident())
