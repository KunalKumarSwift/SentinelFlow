"""Tests for GET /v1/workflows and POST /v1/workflows/{name}/runs."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.incidents import IncidentStatus
from tests.api.conftest import TokenFor
from tests.api.payloads import ALERT


@pytest.fixture
def seeded(client: TestClient, auth: TokenFor, container: ApiContainer) -> TestClient:
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source"))
    container.queue.claim("drain", max_items=10)
    return client


def test_lists_workflows(client: TestClient, auth: TokenFor) -> None:
    response = client.get("/v1/workflows", headers=auth("soc-analyst-l1"))
    assert response.json() == [
        {
            "name": "containment",
            "version": "1.0.0",
            "required_permission": "workflow:run:containment",
        },
        {"name": "triage", "version": "1.0.0", "required_permission": "workflow:run:triage"},
    ]


def test_analyst_can_start_triage_on_new_incident(seeded: TestClient, auth: TokenFor) -> None:
    body = {"incident_id": "inc-0001"}
    response = seeded.post("/v1/workflows/triage/runs", json=body, headers=auth("soc-analyst-l1"))
    assert (response.status_code, response.json()["run_id"]) == (202, "run-0002")


def test_executive_cannot_start_triage(seeded: TestClient, auth: TokenFor) -> None:
    body = {"incident_id": "inc-0001"}
    response = seeded.post("/v1/workflows/triage/runs", json=body, headers=auth("executive"))
    assert response.status_code == 403


def test_unknown_workflow_is_404(seeded: TestClient, auth: TokenFor) -> None:
    body = {"incident_id": "inc-0001"}
    response = seeded.post("/v1/workflows/nope/runs", json=body, headers=auth("soc-analyst-l1"))
    assert response.status_code == 404


def test_unknown_incident_is_404(seeded: TestClient, auth: TokenFor) -> None:
    body = {"incident_id": "inc-9999"}
    response = seeded.post("/v1/workflows/triage/runs", json=body, headers=auth("soc-analyst-l1"))
    assert response.status_code == 404


def test_triage_on_already_triaged_incident_is_409(
    seeded: TestClient, auth: TokenFor, container: ApiContainer
) -> None:
    incident = container.incidents.get("acme", "inc-0001")
    assert incident is not None
    container.incidents.update(replace(incident, status=IncidentStatus.TRIAGED))
    body = {"incident_id": "inc-0001"}
    response = seeded.post("/v1/workflows/triage/runs", json=body, headers=auth("soc-analyst-l1"))
    assert response.status_code == 409
