"""Scan node: look for prompt-injection attempts in the alert's untrusted text."""

from sentinelflow.security.injection import detect_injection
from sentinelflow.workflows.triage.state import TriageInput, TriageUpdate


def scan_for_injection(state: TriageInput) -> TriageUpdate:
    """Record which injection indicators the alert title and raw fields contain."""
    alert = state["alert"]
    return {"injection_indicators": detect_injection([alert.title, *alert.raw.values()])}
