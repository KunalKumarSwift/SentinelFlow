"""Every simulator scenario through the full lifecycle reaches its expected outcome."""

import pytest

from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.registry import SCENARIOS
from tests.integration.lifecycle_harness import Harness
from tests.unit.simulator.conftest import make_context


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_scenario_outcome(name: str) -> None:
    expected = SCENARIOS[name](make_context()).expected
    h = Harness()
    waiting = h.start(name)
    incident = h.incidents.get("acme", "inc-0001")
    assert incident is not None
    assert (incident.severity, incident.verdict) == (expected.severity, expected.verdict)
    proposed = tuple(a.action.kind for a in h.approvals.for_run("acme", "run-1"))
    assert proposed == expected.actions
    assert waiting is bool(expected.actions)
    if not waiting:
        assert incident.status in {IncidentStatus.CLOSED, IncidentStatus.ESCALATED}


def test_critical_key_leak_needs_two_commanders() -> None:
    h = Harness()
    h.start("leaked_key")
    [approval] = h.approvals.pending("acme")
    assert (approval.required_role, approval.required_count) == ("incident-commander", 2)
    incident = h.incidents.get("acme", "inc-0001")
    assert incident is not None and incident.severity is Severity.CRITICAL
