"""Demo path through the real wiring: alert in, investigated incident awaiting approval out."""

from collections.abc import Mapping

from fastapi.testclient import TestClient
from pydantic import SecretStr

from sentinelflow.api.app import create_app
from sentinelflow.bootstrap.wiring import build_runtime
from sentinelflow.core.config import Settings
from sentinelflow.simulator.payload import alert_payload
from sentinelflow.simulator.registry import SCENARIOS
from tests.unit.simulator.conftest import make_context

SETTINGS = Settings(jwt_secret=SecretStr("s" * 32))  # type: ignore[call-arg]
SIM = {
    "subject": "svc-sim",
    "tenant_id": "acme",
    "team": "ops",
    "roles": ["alert-source"],
    "kind": "service",
}
ANALYST = {"subject": "u-ana", "tenant_id": "acme", "team": "soc-emea", "roles": ["soc-analyst-l1"]}


def _token(client: TestClient, identity: Mapping[str, object]) -> dict[str, str]:
    token = client.post("/v1/auth/dev-token", json=identity).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_brute_force_alert_is_triaged_and_investigated_by_the_worker() -> None:
    runtime = build_runtime(SETTINGS, demo_seed=42)
    client = TestClient(create_app(runtime.container))
    alert = SCENARIOS["brute_force"](make_context(42)).alerts[0]
    accepted = client.post("/v1/alerts", json=alert_payload(alert), headers=_token(client, SIM))
    assert accepted.status_code == 202
    assert runtime.worker.run_once() == 1
    incident_id = accepted.json()["incident_id"]
    body = client.get(f"/v1/incidents/{incident_id}", headers=_token(client, ANALYST)).json()
    assert (body["status"], body["severity"], body["verdict"]) == (
        "awaiting_approval",
        "high",
        "needs_review",
    )
