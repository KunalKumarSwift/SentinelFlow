"""``GET /metrics`` exports Prometheus text, including the request just made."""

from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from sentinelflow.api.app import create_app
from sentinelflow.providers.metrics.prometheus_metrics import PrometheusMetrics
from sentinelflow.security.tokens import Hs256TokenService
from tests.api.conftest import TokenFor, make_container


def test_metrics_endpoint_reports_requests(tokens: Hs256TokenService, auth: TokenFor) -> None:
    metrics = PrometheusMetrics(CollectorRegistry())
    client = TestClient(create_app(make_container(tokens, metrics=metrics)))
    client.get("/v1/incidents", headers=auth("soc-analyst-l1"))
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert 'sentinelflow_http_requests_total{group="read",status="200"} 1.0' in response.text
