"""Correlation ids, one access-log line and request metrics per request.

A valid incoming ``X-Correlation-ID`` is reused (so a caller can trace a request across
systems); anything else is replaced. The id is bound into the logging context for the
whole request and echoed on the response.
"""

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from sentinelflow.contracts.metrics import Metrics
from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory
from sentinelflow.core.logging import bound, get_logger, valid_correlation_id
from sentinelflow.security.throttle import route_group

HEADER = "X-Correlation-ID"
_log = get_logger("sentinelflow.api")


def install(app: FastAPI, ids: IdFactory, clock: Clock, metrics: Metrics) -> None:
    """Add the correlation middleware to ``app``."""

    async def correlate(request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(HEADER, "")
        correlation_id = incoming if valid_correlation_id(incoming) else ids.new_id("req")
        started = clock.now()
        with bound(correlation_id=correlation_id):
            response = await call_next(request)
            elapsed = (clock.now() - started).total_seconds()
            group = route_group(request.method, request.url.path)
            metrics.http_request(group, response.status_code, elapsed)
            _log.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                tenant_id=getattr(request.state, "tenant_id", None),
                duration_ms=round(elapsed * 1000, 1),
            )
        response.headers[HEADER] = correlation_id
        return response

    app.middleware("http")(correlate)
