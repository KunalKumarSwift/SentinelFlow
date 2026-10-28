"""Map domain errors to RFC 9457 ``application/problem+json`` responses.

Business code raises typed ``SentinelFlowError`` subclasses and never thinks about
HTTP; this module is the single place that decides status codes.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sentinelflow.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    InvalidTransitionError,
    NotFoundError,
    ProviderError,
    SentinelFlowError,
)

# Most specific first: the first matching class decides the status.
_STATUS: list[tuple[type[SentinelFlowError], int, str]] = [
    (AuthenticationError, 401, "Unauthorized"),
    (AuthorizationError, 403, "Forbidden"),
    (NotFoundError, 404, "Not Found"),
    (InvalidTransitionError, 409, "Conflict"),
    (DomainError, 422, "Unprocessable Content"),
    (ProviderError, 503, "Service Unavailable"),
]


def problem(status: int, title: str, detail: str) -> JSONResponse:
    """Return a problem-details response."""
    body = {"type": "about:blank", "title": title, "status": status, "detail": detail}
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(body, status, headers, media_type="application/problem+json")


def _handle(_: Request, exc: Exception) -> JSONResponse:
    for error_type, status, title in _STATUS:
        if isinstance(exc, error_type):
            return problem(status, title, str(exc))
    return problem(500, "Internal Server Error", "unexpected error")


def install(app: FastAPI) -> None:
    """Register the domain-error handler on ``app``."""
    app.add_exception_handler(SentinelFlowError, _handle)
