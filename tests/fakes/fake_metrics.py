"""Metrics recorder for tests: keeps every call as a tuple."""


class RecordingMetrics:
    """Implements ``Metrics`` by appending ``(method, *labels)`` to ``calls``."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def command_finished(self, command: str, outcome: str, seconds: float) -> None:
        self.calls.append(("command_finished", command, outcome))

    def http_request(self, group: str, status: int, seconds: float) -> None:
        self.calls.append(("http_request", group, status))

    def audit_event(self, verb: str) -> None:
        self.calls.append(("audit_event", verb))

    def llm_tokens(self, tenant_id: str, tokens: int) -> None:
        self.calls.append(("llm_tokens", tenant_id, tokens))

    def exposition(self) -> bytes:
        return b""
