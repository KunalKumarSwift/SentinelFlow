"""Incident lifecycle orchestrator (Phase 1: triage only) on simulator scenarios."""

import pytest

from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.providers.identity.mock_identity import MockIdentity
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from sentinelflow.simulator.registry import SCENARIOS
from sentinelflow.workflows.orchestrator import build_lifecycle_graph, run_lifecycle
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph
from tests.builders import an_incident
from tests.fakes.fake_llm import FakeLLM
from tests.unit.simulator.conftest import make_context
from tests.unit.workflows.triage.helpers import FP, TP


@pytest.mark.parametrize(
    ("name", "answer", "status"),
    [("brute_force", TP, IncidentStatus.TRIAGED), ("benign_travel", FP, IncidentStatus.CLOSED)],
)
def test_lifecycle_applies_triage_to_incident(
    name: str, answer: dict[str, str], status: IncidentStatus
) -> None:
    out = SCENARIOS[name](make_context())
    deps = TriageDeps(
        intel=MockThreatIntel(out.seed_data.ip_reputations),
        identity=MockIdentity(out.seed_data.users),
        llm=FakeLLM({"triage.classify": answer}),
    )
    alert = out.alerts[0]
    graph = build_lifecycle_graph(build_triage_graph(deps))
    incident = run_lifecycle(graph, an_incident(entities=alert.entities), alert)
    assert (incident.status, incident.severity, incident.verdict) == (
        status,
        out.expected.severity,
        out.expected.verdict,
    )
