"""Map domain errors to RFC 9457 ``application/problem+json`` responses.

Business code raises typed ``SentinelFlowError`` subclasses and never thinks about
HTTP; this module is the single place that decides status codes.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sentinelflow.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    InvalidTransitionError,
    NotFoundError,
    ProviderError,
    RateLimitedError,
    SentinelFlowError,
)

# Most specific first: the first matching class decides the status.
_STATUS: list[tuple[type[SentinelFlowError], int, str]] = [
    (AuthenticationError, 401, "Unauthorized"),
    (AuthorizationError, 403, "Forbidden"),
    (NotFoundError, 404, "Not Found"),
    (InvalidTransitionError, 409, "Conflict"),
    (ConflictError, 409, "Conflict"),
    (DomainError, 422, "Unprocessable Content"),
    (RateLimitedError, 429, "Too Many Requests"),
    (ProviderError, 503, "Service Unavailable"),
]


def problem(
    status: int, title: str, detail: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    """Return a problem-details response."""
    body = {"type": "about:blank", "title": title, "status": status, "detail": detail}
    if status == 401:
        headers = {"WWW-Authenticate": "Bearer"}
    return JSONResponse(body, status, headers, media_type="application/problem+json")


def _handle(_: Request, exc: Exception) -> JSONResponse:
    for error_type, status, title in _STATUS:
        if isinstance(exc, error_type):
            return problem(status, title, str(exc), _extra_headers(exc))
    return problem(500, "Internal Server Error", "unexpected error")


def _extra_headers(exc: Exception) -> dict[str, str] | None:
    if isinstance(exc, RateLimitedError):
        return {"Retry-After": str(exc.retry_after)}
    return None


def install(app: FastAPI) -> None:
    """Register the domain-error handler on ``app``."""
    app.add_exception_handler(SentinelFlowError, _handle)
