"""Tests for the ingestion service: dedup and incident upsert."""

from dataclasses import replace
from datetime import timedelta

import pytest

from sentinelflow.domain.errors import UnknownRuleError
from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.domain.severity import Severity
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.workflows.ingestion import IngestionDeps, IngestionService
from tests.builders import T0, an_alert, some_entities
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_ids import SequentialIdFactory


@pytest.fixture
def incidents() -> MemoryIncidentRepository:
    return MemoryIncidentRepository()


@pytest.fixture
def service(incidents: MemoryIncidentRepository) -> IngestionService:
    deps = IngestionDeps(
        alerts=MemoryAlertRepository(),
        incidents=incidents,
        ids=SequentialIdFactory(),
        clock=FakeClock(T0),
        default_team="soc-emea",
    )
    return IngestionService(deps)


def test_first_alert_opens_new_incident(
    service: IngestionService, incidents: MemoryIncidentRepository
) -> None:
    result = service.ingest(an_alert())
    incident = incidents.get("acme", result.incident_id)
    assert result.deduplicated is False
    assert incident is not None
    assert (incident.status, incident.severity, incident.team) == (
        IncidentStatus.NEW,
        Severity.MEDIUM,
        "soc-emea",
    )


def test_repeat_within_window_joins_open_incident(
    service: IngestionService, incidents: MemoryIncidentRepository
) -> None:
    first = service.ingest(an_alert(id="alt-1"))
    again = service.ingest(an_alert(id="alt-2", observed_at=T0 + timedelta(minutes=5)))
    assert (again.deduplicated, again.incident_id) == (True, first.incident_id)
    incident = incidents.get("acme", first.incident_id)
    assert incident is not None and incident.alert_ids == ("alt-1", "alt-2")


def test_repeat_after_window_opens_new_incident(service: IngestionService) -> None:
    first = service.ingest(an_alert(id="alt-1"))
    later = service.ingest(an_alert(id="alt-2", observed_at=T0 + timedelta(hours=1)))
    assert later.deduplicated is False and later.incident_id != first.incident_id


def test_repeat_of_closed_incident_opens_new_incident(
    service: IngestionService, incidents: MemoryIncidentRepository
) -> None:
    first = service.ingest(an_alert(id="alt-1"))
    closed = incidents.get("acme", first.incident_id)
    assert closed is not None
    incidents.update(replace(closed, status=IncidentStatus.CLOSED))
    again = service.ingest(an_alert(id="alt-2", observed_at=T0 + timedelta(minutes=1)))
    assert again.deduplicated is False and again.incident_id != first.incident_id


def test_different_entities_open_separate_incidents(service: IngestionService) -> None:
    first = service.ingest(an_alert(id="alt-1"))
    other = service.ingest(an_alert(id="alt-2", entities=some_entities(user="bob")))
    assert other.incident_id != first.incident_id


def test_unknown_rule_is_rejected_before_anything_is_stored(
    service: IngestionService, incidents: MemoryIncidentRepository
) -> None:
    with pytest.raises(UnknownRuleError):
        service.ingest(an_alert(rule_id="made_up_rule"))
    assert incidents.get("acme", "inc-0001") is None
