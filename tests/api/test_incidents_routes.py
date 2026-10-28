"""Tests for GET /v1/incidents and GET /v1/incidents/{id}."""

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import TokenFor
from tests.api.payloads import ALERT


@pytest.fixture
def seeded(client: TestClient, auth: TokenFor) -> TestClient:
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source", tenant="acme"))
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source", tenant="globex"))
    return client


def test_get_incident_returns_details(seeded: TestClient, auth: TokenFor) -> None:
    response = seeded.get("/v1/incidents/inc-0001", headers=auth("soc-analyst-l1"))
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["severity"], body["team"]) == ("new", "medium", "soc-emea")
    assert body["entities"]["user"] == "alice"


def test_other_tenants_incident_is_404(seeded: TestClient, auth: TokenFor) -> None:
    response = seeded.get("/v1/incidents/inc-0002", headers=auth("soc-analyst-l1", tenant="acme"))
    assert response.status_code == 404


def test_list_shows_only_own_tenant(seeded: TestClient, auth: TokenFor) -> None:
    response = seeded.get("/v1/incidents", headers=auth("soc-analyst-l1", tenant="globex"))
    assert [i["id"] for i in response.json()["items"]] == ["inc-0002"]


def test_auditor_cannot_read_incidents(seeded: TestClient, auth: TokenFor) -> None:
    assert seeded.get("/v1/incidents", headers=auth("auditor")).status_code == 403
