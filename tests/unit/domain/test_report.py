"""Tests for the deterministic, verified facts section of incident reports."""

from sentinelflow.domain.report import ActionLine, ReportFacts, render_facts

FACTS = ReportFacts(
    incident_id="inc-1",
    status="closed",
    severity="high",
    verdict="needs_review",
    injection=("verdict_steering",),
    techniques=("T1110", "T1078"),
    actions=(
        ActionLine("disable_user", "user-1a2b", "approved"),
        ActionLine("block_ip", "203.0.113.9", "rejected"),
    ),
    executed=("inc-1:disable_user",),
)


def test_facts_section_lists_every_fact() -> None:
    text = render_facts(FACTS)
    assert text.startswith("## Facts (verified from the audit trail)")
    for expected in ("inc-1", "high", "needs_review", "verdict_steering", "T1110, T1078"):
        assert expected in text
    assert "| disable_user | user-1a2b | approved |" in text
    assert "inc-1:disable_user" in text


def test_empty_facts_say_none() -> None:
    empty = ReportFacts("inc-2", "escalated", "low", "true_positive", (), (), (), ())
    text = render_facts(empty)
    assert "Prompt-injection indicators: none" in text and "No actions were proposed." in text
