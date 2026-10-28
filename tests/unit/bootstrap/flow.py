"""A running single-process runtime with helpers for tokens and API calls."""

from collections.abc import Mapping

from fastapi.testclient import TestClient
from pydantic import SecretStr

from sentinelflow.api.app import create_app
from sentinelflow.bootstrap.wiring import Runtime, build_runtime
from sentinelflow.core.config import Settings
from sentinelflow.simulator.payload import alert_payload
from sentinelflow.simulator.registry import SCENARIOS
from tests.unit.simulator.conftest import make_context

SETTINGS = Settings(jwt_secret=SecretStr("s" * 32))  # type: ignore[call-arg]


def who(subject: str, *roles: str, tenant: str = "acme") -> Mapping[str, object]:
    """Return a dev-token identity."""
    return {"subject": subject, "tenant_id": tenant, "team": "soc-emea", "roles": list(roles)}


class Flow:
    """Drives the API and the worker together."""

    def __init__(self, settings: Settings = SETTINGS) -> None:
        """Wire a fresh runtime."""
        self.runtime: Runtime = build_runtime(settings, demo_seed=42)
        self.client = TestClient(create_app(self.runtime.container))
        self.alert = SCENARIOS["brute_force"](make_context(42)).alerts[0]

    def auth(self, identity: Mapping[str, object]) -> dict[str, str]:
        """Return bearer headers for ``identity``."""
        token = self.client.post("/v1/auth/dev-token", json=identity).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def ingest(self) -> dict[str, str]:
        """Post the brute-force alert and let the worker process it."""
        sim = {**who("svc-sim", "alert-source"), "kind": "service"}
        body = self.client.post(
            "/v1/alerts", json=alert_payload(self.alert), headers=self.auth(sim)
        )
        self.runtime.worker.run_once()
        return body.json()

    def approvals(self, identity: Mapping[str, object]) -> list[dict[str, object]]:
        """Return the approvals ``identity`` may decide."""
        return self.client.get("/v1/approvals", headers=self.auth(identity)).json()["items"]

    def decide(
        self, approval_id: object, identity: Mapping[str, object], approved: bool = True
    ) -> int:
        """Decide an approval and return the HTTP status."""
        body = {"approved": approved, "reason": "checked the evidence"}
        url = f"/v1/approvals/{approval_id}/decision"
        return self.client.post(url, json=body, headers=self.auth(identity)).status_code
