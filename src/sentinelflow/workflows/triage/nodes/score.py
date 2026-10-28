"""Scoring node: deterministic severity from rule, entities and enrichment."""

from sentinelflow.domain.enrichment import Enrichment
from sentinelflow.domain.scoring import score_severity
from sentinelflow.workflows.triage.state import ScoreInput, TriageUpdate


def score(state: ScoreInput) -> TriageUpdate:
    """Compute severity with ``domain.scoring``; the LLM never influences it."""
    enrichment = Enrichment(ip_reputation=state["ip_reputation"], user=state["user"])
    alert = state["alert"]
    return {"severity": score_severity(alert.rule_id, state["incident"].entities, enrichment)}
