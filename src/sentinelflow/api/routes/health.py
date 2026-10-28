"""Liveness and metrics endpoints (public; restrict ``/metrics`` at the network edge)."""

from fastapi import APIRouter, Response

from sentinelflow.contracts.metrics import Metrics

PROMETHEUS_TEXT = "text/plain; version=0.0.4; charset=utf-8"


def build_health_router(metrics: Metrics) -> APIRouter:
    """Return the router serving ``GET /healthz`` and ``GET /metrics``."""
    router = APIRouter(tags=["health"])

    @router.get("/healthz")
    def healthz() -> dict[str, str]:
        """Report that the process is up."""
        return {"status": "ok"}

    @router.get("/metrics", include_in_schema=False)
    def prometheus() -> Response:
        """Export this process's metrics in Prometheus text format."""
        return Response(metrics.exposition(), media_type=PROMETHEUS_TEXT)

    return router
