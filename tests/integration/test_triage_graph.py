"""Triage graph end to end on simulator scenarios, with mock providers and FakeLLM."""

import pytest

from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.providers.identity.mock_identity import MockIdentity
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from sentinelflow.simulator.output import ScenarioOutput
from sentinelflow.simulator.registry import SCENARIOS
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph, run_triage
from tests.builders import an_incident
from tests.fakes.fake_llm import FakeLLM
from tests.unit.simulator.conftest import make_context
from tests.unit.workflows.triage.helpers import FP, TP


def _triage(out: ScenarioOutput, llm_answer: dict[str, str]) -> tuple[Severity, Verdict]:
    deps = TriageDeps(
        intel=MockThreatIntel(out.seed_data.ip_reputations),
        identity=MockIdentity(out.seed_data.users),
        llm=FakeLLM({"triage.classify": llm_answer}),
    )
    alert = out.alerts[0]
    incident = an_incident(entities=alert.entities, alert_ids=(alert.id,))
    result = run_triage(build_triage_graph(deps), incident, alert)
    return result.severity, result.verdict


@pytest.mark.parametrize(("name", "llm_answer"), [("brute_force", TP), ("benign_travel", FP)])
def test_scenario_reaches_expected_outcome(name: str, llm_answer: dict[str, str]) -> None:
    out = SCENARIOS[name](make_context())
    assert _triage(out, llm_answer) == (out.expected.severity, out.expected.verdict)


def test_llm_cannot_dismiss_a_high_severity_attack() -> None:
    out = SCENARIOS["brute_force"](make_context())
    assert _triage(out, FP) == (Severity.HIGH, Verdict.NEEDS_REVIEW)
