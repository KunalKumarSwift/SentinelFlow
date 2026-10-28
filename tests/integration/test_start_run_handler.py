"""StartRunHandler runs the lifecycle for a queued incident and saves the result."""

import pytest

from sentinelflow.contracts.repositories import StoredAlert
from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.providers.identity.mock_identity import MockIdentity
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.runtime.start_handler import StartRunHandler
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.simulator.registry import SCENARIOS
from sentinelflow.workflows.orchestrator import build_lifecycle_graph
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph
from tests.builders import T0, an_incident
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_llm import FakeLLM
from tests.unit.simulator.conftest import make_context
from tests.unit.workflows.triage.helpers import TP

AUDIT = MemoryAuditStore()


def _handler() -> tuple[StartRunHandler, MemoryIncidentRepository, StartRun]:
    out = SCENARIOS["brute_force"](make_context())
    alert = out.alerts[0]
    alerts, incidents = MemoryAlertRepository(), MemoryIncidentRepository()
    alerts.add(StoredAlert(alert, "fp", "inc-0001"))
    incidents.add(an_incident(entities=alert.entities, alert_ids=(alert.id,)))
    deps = TriageDeps(
        intel=MockThreatIntel(out.seed_data.ip_reputations),
        identity=MockIdentity(out.seed_data.users),
        llm=FakeLLM({"triage.classify": TP}),
    )
    graph = build_lifecycle_graph(build_triage_graph(deps))
    cmd = StartRun("run-1", "acme", "triage", "inc-0001", alert.id, "svc-orchestrator")
    recorder = AuditRecorder(AUDIT, FakeClock(T0))
    return StartRunHandler(alerts, incidents, graph, recorder), incidents, cmd


def test_handler_triages_and_saves_incident() -> None:
    handler, incidents, cmd = _handler()
    handler(cmd)
    saved = incidents.get("acme", "inc-0001")
    assert saved is not None and saved.status is IncidentStatus.TRIAGED
    last = AUDIT.read("acme", after_seq=0, limit=100)[-1]
    assert (last.verb, last.actor, last.details["severity"]) == (
        "incident.triaged",
        "svc-orchestrator",
        "high",
    )


def test_missing_incident_is_a_permanent_error() -> None:
    handler, _, cmd = _handler()
    with pytest.raises(NotFoundError, match="incident"):
        handler(StartRun("run-2", "acme", "triage", "inc-9999", cmd.alert_id, "svc"))


def test_missing_alert_is_a_permanent_error() -> None:
    handler, _, cmd = _handler()
    with pytest.raises(NotFoundError, match="alert"):
        handler(StartRun("run-2", "acme", "triage", cmd.incident_id, "alt-9999", "svc"))
