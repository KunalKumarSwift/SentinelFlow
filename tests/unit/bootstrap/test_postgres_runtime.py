"""STORAGE_BACKEND=postgres: the same flow, and a paused run survives a process restart."""

from pydantic import SecretStr

from sentinelflow.bootstrap.wiring import build_runtime
from sentinelflow.contracts.run_queue import ResumeRun
from sentinelflow.core.config import Settings
from tests.contracts.pg import database_url
from tests.unit.bootstrap.flow import Flow, who

CMDR = who("u-cmdr", "incident-commander")
L2 = who("u-l2", "soc-analyst-l2")


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        jwt_secret=SecretStr("s" * 32),
        storage_backend="postgres",
        database_url=SecretStr(database_url()),
    )


def test_paused_run_resumes_in_a_fresh_runtime() -> None:
    settings = _settings()
    first = Flow(settings)
    accepted = first.ingest()
    pending = {a["action"]: a["id"] for a in first.approvals(CMDR)}
    assert first.decide(pending["disable_user"], CMDR) == 200
    assert first.decide(pending["block_ip"], L2) == 200
    # The first process "crashes" before its worker resumes; a new one picks the run up.
    second = build_runtime(settings, demo_seed=42)
    second.container.queue.publish(ResumeRun(accepted["run_id"], "acme", str(pending["block_ip"])))
    assert second.worker.run_once() == 1
    run = second.container.runs.get("acme", accepted["run_id"])
    incident = second.container.incidents.get("acme", accepted["incident_id"])
    assert run is not None and run.status.value == "completed"
    assert incident is not None and incident.status.value == "closed"
