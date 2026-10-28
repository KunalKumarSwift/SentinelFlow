"""Outcome of triaging an incident."""

from dataclasses import dataclass

from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity


@dataclass(frozen=True, slots=True)
class TriageResult:
    """Severity (from rules) and verdict (from the LLM, overridden when unsafe)."""

    severity: Severity
    verdict: Verdict
    rationale: str
