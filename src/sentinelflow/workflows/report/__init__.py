"""Post-incident reporting: verified facts plus an optional LLM narrative."""

from sentinelflow.workflows.report.facts import collect_facts
from sentinelflow.workflows.report.writer import write_report

__all__ = ["collect_facts", "write_report"]
