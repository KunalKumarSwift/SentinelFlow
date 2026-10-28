"""Interface for operational metrics (Prometheus in production, a recorder in tests)."""

from typing import Protocol


class Metrics(Protocol):
    """Counters and histograms the platform reports; label values stay low-cardinality."""

    def command_finished(self, command: str, outcome: str, seconds: float) -> None:
        """Record one processed run command (``outcome``: done / retry / dead_lettered)."""
        ...

    def http_request(self, group: str, status: int, seconds: float) -> None:
        """Record one API request by route group and status code."""
        ...

    def audit_event(self, verb: str) -> None:
        """Record one audit event, e.g. ``policy.denied`` or ``incident.contained``."""
        ...

    def llm_tokens(self, tenant_id: str, tokens: int) -> None:
        """Record tokens reserved for a tenant's LLM call."""
        ...

    def exposition(self) -> bytes:
        """Return the metrics in Prometheus text format (empty if not exported)."""
        ...
