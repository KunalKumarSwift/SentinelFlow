"""The report is the LLM narrative plus verified facts, or the facts alone."""

from sentinelflow.domain.errors import ProviderError
from sentinelflow.domain.report import ReportFacts
from sentinelflow.workflows.report.writer import write_report
from tests.fakes.fake_llm import FakeLLM

FACTS = ReportFacts("inc-1", "closed", "high", "true_positive", (), ("T1110",), (), ())


def test_narrative_is_followed_by_verified_facts() -> None:
    llm = FakeLLM({"report.write": {"markdown": "# Summary\nBrute force contained."}})
    body = write_report(llm, FACTS)
    assert body.startswith("# Summary") and "## Facts (verified" in body
    assert "T1110" in llm.prompts[0].untrusted["facts"]


def test_llm_failure_still_produces_a_factual_report() -> None:
    llm = FakeLLM({"report.write": ProviderError("down", retryable=True)})
    body = write_report(llm, FACTS)
    assert body.startswith("# Incident inc-1") and "## Facts (verified" in body
