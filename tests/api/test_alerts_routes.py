"""Tests for POST /v1/alerts."""

from fastapi.testclient import TestClient

from sentinelflow.api.container import ApiContainer
from sentinelflow.contracts.run_queue import StartRun
from tests.api.conftest import TokenFor
from tests.api.payloads import ALERT


def test_new_alert_opens_incident_and_queues_triage(
    client: TestClient, auth: TokenFor, container: ApiContainer
) -> None:
    response = client.post("/v1/alerts", json=ALERT, headers=auth("alert-source", kind="service"))
    assert response.status_code == 202
    body = response.json()
    assert (body["incident_id"], body["deduplicated"], body["run_id"]) == (
        "inc-0001",
        False,
        "run-0001",
    )
    [delivery] = container.queue.claim("test", max_items=10)
    assert isinstance(delivery.command, StartRun)
    assert (delivery.command.workflow, delivery.command.incident_id) == ("triage", "inc-0001")


def test_duplicate_alert_joins_incident_without_new_run(
    client: TestClient, auth: TokenFor, container: ApiContainer
) -> None:
    headers = auth("alert-source", kind="service")
    client.post("/v1/alerts", json=ALERT, headers=headers)
    second = client.post("/v1/alerts", json=ALERT, headers=headers).json()
    assert (second["deduplicated"], second["run_id"]) == (True, None)
    assert len(container.queue.claim("test", max_items=10)) == 1


def test_tenant_comes_from_token_not_body(
    client: TestClient, auth: TokenFor, container: ApiContainer
) -> None:
    body = {**ALERT, "tenant_id": "globex"}
    response = client.post("/v1/alerts", json=body, headers=auth("alert-source", tenant="acme"))
    assert response.status_code == 422
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source", tenant="acme"))
    assert container.incidents.get("acme", "inc-0001") is not None


def test_analyst_cannot_ingest(client: TestClient, auth: TokenFor) -> None:
    assert client.post("/v1/alerts", json=ALERT, headers=auth("soc-analyst-l1")).status_code == 403


def test_unknown_rule_is_422(client: TestClient, auth: TokenFor) -> None:
    body = {**ALERT, "rule_id": "made_up_rule"}
    assert client.post("/v1/alerts", json=body, headers=auth("alert-source")).status_code == 422


def test_naive_timestamp_is_422(client: TestClient, auth: TokenFor) -> None:
    body = {**ALERT, "observed_at": "2026-01-01T09:00:00"}
    assert client.post("/v1/alerts", json=body, headers=auth("alert-source")).status_code == 422
