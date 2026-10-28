"""Prometheus metrics: each call shows up as the expected sample."""

from prometheus_client import CollectorRegistry

from sentinelflow.providers.metrics.null_metrics import NullMetrics
from sentinelflow.providers.metrics.prometheus_metrics import PrometheusMetrics


def _metrics() -> tuple[PrometheusMetrics, CollectorRegistry]:
    registry = CollectorRegistry()
    return PrometheusMetrics(registry), registry


def test_commands_are_counted_by_type_and_outcome() -> None:
    metrics, registry = _metrics()
    metrics.command_finished("StartRun", "done", 0.25)
    labels = {"command": "StartRun", "outcome": "done"}
    assert registry.get_sample_value("sentinelflow_run_commands_total", labels) == 1
    assert registry.get_sample_value("sentinelflow_run_command_seconds_count", labels) == 1


def test_http_requests_audit_events_and_tokens_are_counted() -> None:
    metrics, registry = _metrics()
    metrics.http_request("read", 200, 0.01)
    metrics.audit_event("policy.denied")
    metrics.llm_tokens("acme", 1500)
    assert (
        registry.get_sample_value(
            "sentinelflow_http_requests_total", {"group": "read", "status": "200"}
        )
        == 1
    )
    assert (
        registry.get_sample_value("sentinelflow_audit_events_total", {"verb": "policy.denied"}) == 1
    )
    assert registry.get_sample_value("sentinelflow_llm_tokens_total", {"tenant_id": "acme"}) == 1500


def test_exposition_is_prometheus_text() -> None:
    metrics, _ = _metrics()
    metrics.audit_event("alert.ingested")
    assert b'sentinelflow_audit_events_total{verb="alert.ingested"} 1.0' in metrics.exposition()


def test_null_metrics_accept_everything_and_export_nothing() -> None:
    metrics = NullMetrics()
    metrics.command_finished("StartRun", "done", 0.1)
    metrics.http_request("read", 200, 0.1)
    metrics.audit_event("x")
    metrics.llm_tokens("acme", 1)
    assert metrics.exposition() == b""


def test_queue_depth_is_read_at_scrape_time() -> None:
    metrics, registry = _metrics()
    depth = [4]
    metrics.track_queue_depth(lambda: depth[0])
    assert registry.get_sample_value("sentinelflow_queue_messages") == 4
    depth[0] = 1
    assert registry.get_sample_value("sentinelflow_queue_messages") == 1
