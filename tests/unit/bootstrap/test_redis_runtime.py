"""Scaled-out shape: Postgres + Redis, with the API and the worker in separate runtimes."""

import os

from pydantic import SecretStr

from sentinelflow.bootstrap.wiring import build_runtime
from sentinelflow.core.config import Settings
from sentinelflow.simulator.payload import alert_payload
from tests.contracts.pg import database_url
from tests.contracts.redis_backend import fresh_redis
from tests.unit.bootstrap.flow import Flow, who


def _settings() -> Settings:
    fresh_redis()
    return Settings(  # type: ignore[call-arg]
        jwt_secret=SecretStr("s" * 32),
        storage_backend="postgres",
        database_url=SecretStr(database_url()),
        queue_backend="redis",
        redis_url=os.environ["TEST_REDIS_URL"],
    )


def test_alert_accepted_by_the_api_is_processed_by_a_separate_worker() -> None:
    settings = _settings()
    api = Flow(settings)
    worker = build_runtime(settings, demo_seed=42).worker
    sim = {**who("svc-sim", "alert-source"), "kind": "service"}
    headers = api.auth(sim)
    accepted = api.client.post("/v1/alerts", json=alert_payload(api.alert), headers=headers)
    assert worker.run_once() == 1
    run = api.client.get(
        f"/v1/runs/{accepted.json()['run_id']}", headers=api.auth(who("u", "soc-analyst-l1"))
    )
    assert run.json()["status"] == "waiting"
    assert api.runtime.worker.run_once() == 0
