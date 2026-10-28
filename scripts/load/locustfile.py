r"""Load test: detection sources posting alerts while analysts read incidents.

    uv run locust -f scripts/load/locustfile.py --headless -u 20 -r 5 -t 60s \\
        --host http://127.0.0.1:8000

Every alert comes from a fresh simulator seed, so none is deduplicated and each one
starts a lifecycle run; run ``scripts/load/run_stats.py`` afterwards for worker throughput.
"""

import itertools
from collections.abc import Mapping
from random import Random

from locust import HttpUser, between, task

from sentinelflow.core.clock import SystemClock
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.payload import alert_payload
from sentinelflow.simulator.registry import SCENARIOS

_SEEDS = itertools.count(1_000_000)
_SOURCE = {"subject": "svc-load", "tenant_id": "acme", "team": "ops", "roles": ["alert-source"]}
_ANALYST = {
    "subject": "u-load",
    "tenant_id": "acme",
    "team": "soc-emea",
    "roles": ["soc-analyst-l1"],
}


class SocTraffic(HttpUser):
    """One detection source / analyst pair."""

    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        """Get tokens for both identities from the dev-token endpoint."""
        self.source = self._token({**_SOURCE, "kind": "service"})
        self.analyst = self._token(_ANALYST)

    @task(3)
    def post_alert(self) -> None:
        """Post one brute-force alert with never-seen-before entities."""
        ctx = ScenarioContext(Random(next(_SEEDS)), SystemClock(), UuidIdFactory(), "acme")
        alert = SCENARIOS["brute_force"](ctx).alerts[0]
        self.client.post("/v1/alerts", json=alert_payload(alert), headers=self.source)

    @task(1)
    def list_incidents(self) -> None:
        """Read the incident list like an analyst's dashboard."""
        self.client.get("/v1/incidents", headers=self.analyst)

    def _token(self, identity: Mapping[str, object]) -> dict[str, str]:
        response = self.client.post("/v1/auth/dev-token", json=identity)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
