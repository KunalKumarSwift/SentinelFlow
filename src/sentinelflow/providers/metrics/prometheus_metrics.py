"""Prometheus metrics on an injected registry (one per process; tests use their own)."""

from collections.abc import Callable

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

_PREFIX = "sentinelflow"


class PrometheusMetrics:
    """``Metrics`` backed by ``prometheus_client`` counters and histograms."""

    def __init__(self, registry: CollectorRegistry) -> None:
        """Register every metric on ``registry``."""
        self.registry = registry
        self._commands = Counter(
            f"{_PREFIX}_run_commands",
            "Processed run commands",
            ["command", "outcome"],
            registry=registry,
        )
        self._command_seconds = Histogram(
            f"{_PREFIX}_run_command_seconds",
            "Time to process a run command",
            ["command", "outcome"],
            registry=registry,
        )
        self._http = Counter(
            f"{_PREFIX}_http_requests", "API requests", ["group", "status"], registry=registry
        )
        self._http_seconds = Histogram(
            f"{_PREFIX}_http_request_seconds", "API latency", ["group"], registry=registry
        )
        self._audit = Counter(
            f"{_PREFIX}_audit_events", "Audit events", ["verb"], registry=registry
        )
        self._tokens = Counter(
            f"{_PREFIX}_llm_tokens",
            "Estimated LLM tokens reserved",
            ["tenant_id"],
            registry=registry,
        )

    def command_finished(self, command: str, outcome: str, seconds: float) -> None:
        """Count a processed command and observe its duration."""
        self._commands.labels(command, outcome).inc()
        self._command_seconds.labels(command, outcome).observe(seconds)

    def http_request(self, group: str, status: int, seconds: float) -> None:
        """Count an API request and observe its latency."""
        self._http.labels(group, str(status)).inc()
        self._http_seconds.labels(group).observe(seconds)

    def audit_event(self, verb: str) -> None:
        """Count an audit event."""
        self._audit.labels(verb).inc()

    def llm_tokens(self, tenant_id: str, tokens: int) -> None:
        """Add reserved tokens for ``tenant_id``."""
        self._tokens.labels(tenant_id).inc(tokens)

    def track_queue_depth(self, depth: Callable[[], int]) -> None:
        """Export ``depth()`` as ``sentinelflow_queue_messages``, read at scrape time.

        KEDA scales workers on this gauge (Prometheus scaler), since the queue is a
        sorted set its Redis scaler cannot read.
        """
        gauge = Gauge(
            f"{_PREFIX}_queue_messages", "Queued or in-flight run commands", registry=self.registry
        )
        gauge.set_function(lambda: float(depth()))

    def exposition(self) -> bytes:
        """Return every metric in Prometheus text format."""
        return generate_latest(self.registry)
