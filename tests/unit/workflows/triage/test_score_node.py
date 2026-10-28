"""Tests for the scoring node."""

from sentinelflow.domain.enrichment import IpReputation
from sentinelflow.domain.severity import Severity
from sentinelflow.workflows.triage.nodes.score import score
from sentinelflow.workflows.triage.state import ScoreInput
from tests.builders import an_alert, an_incident


def test_score_uses_rule_entities_and_enrichment() -> None:
    state: ScoreInput = {
        "incident": an_incident(),
        "alert": an_alert(),
        "ip_reputation": IpReputation(ip="203.0.113.9", score=95),
        "user": None,
    }
    assert score(state) == {"severity": Severity.HIGH}
