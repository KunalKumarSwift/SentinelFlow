"""The access-review graph lists a tenant's accounts and raises one alert per finding."""

from datetime import timedelta

from sentinelflow.domain.access_review import Account
from sentinelflow.providers.identity.mock_accounts import MockAccountDirectory
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.workflows.access_review import (
    AccessReviewDeps,
    AccessReviewGraph,
    build_access_review_graph,
    run_access_review,
)
from sentinelflow.workflows.ingestion import IngestionDeps, IngestionService
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_ids import SequentialIdFactory

ACCOUNTS = (
    Account("alice", "acme", frozenset({"soc-analyst-l1"}), T0 - timedelta(days=1), None),
    Account("bob", "acme", frozenset({"soc-analyst-l2"}), None, None),
    Account("erin", "acme", frozenset({"incident-commander"}), T0, T0 - timedelta(days=40)),
    Account("gus", "globex", frozenset({"auditor"}), None, None),
)


def _graph(clock: FakeClock | None = None) -> tuple[AccessReviewGraph, MemoryIncidentRepository]:
    incidents, alerts, clock = (
        MemoryIncidentRepository(),
        MemoryAlertRepository(),
        clock or FakeClock(T0),
    )
    ingest = IngestionService(IngestionDeps(alerts, incidents, SequentialIdFactory(), clock, "iam"))
    directory = MockAccountDirectory(ACCOUNTS)
    deps = AccessReviewDeps(directory, ingest, alerts, incidents, SequentialIdFactory(), clock)
    return build_access_review_graph(deps), incidents


def test_each_finding_becomes_a_low_severity_incident() -> None:
    graph, incidents = _graph()
    result = run_access_review(graph, "acme")
    assert [(f.rule_id, f.user_id) for f in result.findings] == [
        ("dormant_account", "bob"),
        ("over_privileged_account", "erin"),
    ]
    created = incidents.list("acme")
    assert [i.id for i in created] == list(result.new_incident_ids)
    assert {i.entities.user for i in created} == {"bob", "erin"}
    assert all(i.severity.name == "LOW" and i.team == "iam" for i in created)


def test_repeating_the_review_does_not_duplicate_open_incidents() -> None:
    graph, incidents = _graph()
    run_access_review(graph, "acme")
    again = run_access_review(graph, "acme")
    assert again.new_incident_ids == () and len(incidents.list("acme")) == 2


def test_next_days_review_skips_findings_that_are_still_open() -> None:
    clock = FakeClock(T0)
    graph, incidents = _graph(clock)
    run_access_review(graph, "acme")
    clock.advance(timedelta(days=1))
    assert run_access_review(graph, "acme").new_incident_ids == ()
    assert len(incidents.list("acme")) == 2
