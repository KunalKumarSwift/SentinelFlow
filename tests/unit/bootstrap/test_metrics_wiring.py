"""The wired runtime exports worker, audit and HTTP metrics on ``/metrics``."""

from tests.unit.bootstrap.flow import Flow


def test_processing_an_alert_shows_up_in_metrics() -> None:
    flow = Flow()
    flow.ingest()
    text = flow.client.get("/metrics").text
    assert 'sentinelflow_run_commands_total{command="StartRun",outcome="done"} 1.0' in text
    assert 'sentinelflow_audit_events_total{verb="alert.ingested"} 1.0' in text
    assert 'sentinelflow_http_requests_total{group="ingest",status="202"} 1.0' in text
    assert flow.runtime.metrics.registry is not None
