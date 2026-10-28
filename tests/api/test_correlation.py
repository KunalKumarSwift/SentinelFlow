"""Every response carries a correlation id, and the access log line names the tenant."""

from fastapi.testclient import TestClient

from sentinelflow.core.logging import valid_correlation_id
from tests.api.conftest import TokenFor
from tests.fakes.log_capture import capture_logs


def test_a_correlation_id_is_generated(client: TestClient) -> None:
    response = client.get("/healthz")
    assert valid_correlation_id(response.headers["X-Correlation-ID"])


def test_a_valid_incoming_id_is_kept(client: TestClient) -> None:
    response = client.get("/healthz", headers={"X-Correlation-ID": "abc-123"})
    assert response.headers["X-Correlation-ID"] == "abc-123"


def test_an_invalid_incoming_id_is_replaced(client: TestClient) -> None:
    response = client.get("/healthz", headers={"X-Correlation-ID": "evil\tvalue"})
    assert response.headers["X-Correlation-ID"] != "evil\tvalue"


def test_access_log_names_correlation_id_tenant_and_status(
    client: TestClient, auth: TokenFor
) -> None:
    with capture_logs() as logs:
        headers = {**auth("soc-analyst-l1"), "X-Correlation-ID": "req-1"}
        client.get("/v1/incidents", headers=headers)
    [line] = logs.named("http.request")
    assert (line["correlation_id"], line["tenant_id"], line["status"]) == ("req-1", "acme", 200)
    assert (line["method"], line["path"]) == ("GET", "/v1/incidents")
