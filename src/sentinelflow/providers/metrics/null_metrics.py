"""Metrics that go nowhere: the default when nothing is exported."""


class NullMetrics:
    """``Metrics`` that ignores every call."""

    def command_finished(self, command: str, outcome: str, seconds: float) -> None:
        """Ignore."""

    def http_request(self, group: str, status: int, seconds: float) -> None:
        """Ignore."""

    def audit_event(self, verb: str) -> None:
        """Ignore."""

    def llm_tokens(self, tenant_id: str, tokens: int) -> None:
        """Ignore."""

    def exposition(self) -> bytes:
        """Return nothing."""
        return b""
