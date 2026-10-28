"""Investigation graph end to end on the brute-force scenario."""

from sentinelflow.domain.actions import ActionKind as K
from sentinelflow.simulator.registry import SCENARIOS
from sentinelflow.workflows.investigation import build_investigation_graph, run_investigation
from tests.builders import an_incident
from tests.unit.simulator.conftest import make_context
from tests.unit.workflows.investigation.helpers import deps


def test_brute_force_investigation() -> None:
    out = SCENARIOS["brute_force"](make_context())
    alert = out.alerts[0]
    investigation, _ = deps(out.events)
    incident = an_incident(entities=alert.entities, alert_ids=(alert.id,))
    result = run_investigation(build_investigation_graph(investigation), incident, alert)
    assert [a.kind for a in result.actions] == [K.DISABLE_USER, K.BLOCK_IP]
    assert result.techniques[0].technique_id == "T1110"
    assert result.timeline[0].summary.startswith("login_failed x")
    assert result.timeline[-1].summary.startswith("login_succeeded")
