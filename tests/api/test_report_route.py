"""GET /v1/incidents/{id}/report returns the incident's ticket."""

from fastapi.testclient import TestClient

from sentinelflow.api.container import ApiContainer
from tests.api.conftest import TokenFor
from tests.builders import an_incident


def test_report_is_returned_when_written(
    client: TestClient, auth: TokenFor, container: ApiContainer
) -> None:
    container.incidents.add(an_incident())
    container.ticketing.upsert("acme", "inc-0001", "[high] inc-0001", "# Report")
    body = client.get("/v1/incidents/inc-0001/report", headers=auth("executive")).json()
    assert (body["title"], body["body"]) == ("[high] inc-0001", "# Report")


def test_missing_report_is_404(client: TestClient, auth: TokenFor, container: ApiContainer) -> None:
    container.incidents.add(an_incident())
    assert client.get("/v1/incidents/inc-0001/report", headers=auth("executive")).status_code == 404


def test_report_needs_incident_read(client: TestClient, auth: TokenFor) -> None:
    assert client.get("/v1/incidents/inc-0001/report", headers=auth("auditor")).status_code == 403
