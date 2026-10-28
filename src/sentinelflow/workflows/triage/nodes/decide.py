"""Decision node: combine rule-based severity with the LLM verdict, failing safe.

The LLM may dismiss an incident only when rules scored it below HIGH. A missing or
unusable answer, or any sign of prompt injection in the alert, always means human
review. A prompt injection can therefore at worst cause extra review work, never
silently close a serious attack.
"""

from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.domain.triage import TriageResult
from sentinelflow.workflows.triage.state import DecideInput, TriageUpdate

UNAVAILABLE = "LLM classification unavailable; routed to human review."
INJECTION = "Possible prompt injection in alert data; routed to human review"
OVERRIDDEN = "LLM suggested dismissal, but severity is too high to close without review."


def decide(state: DecideInput) -> TriageUpdate:
    """Produce the final ``TriageResult``."""
    severity, classification = state["severity"], state["classification"]
    indicators = state["injection_indicators"]
    if indicators:
        reason = f"{INJECTION} ({', '.join(indicators)})."
        return _result(severity, Verdict.NEEDS_REVIEW, reason, indicators)
    if classification is None:
        return _result(severity, Verdict.NEEDS_REVIEW, UNAVAILABLE)
    if classification.verdict is Verdict.FALSE_POSITIVE and severity >= Severity.HIGH:
        return _result(severity, Verdict.NEEDS_REVIEW, OVERRIDDEN)
    return _result(severity, classification.verdict, classification.rationale)


def _result(
    severity: Severity, verdict: Verdict, rationale: str, indicators: tuple[str, ...] = ()
) -> TriageUpdate:
    return {"result": TriageResult(severity, verdict, rationale, indicators)}
