"""Structured logging: one JSON object per line, with request/run context on every line.

Context (``correlation_id``, ``tenant_id``, ``run_id`` ...) is bound with ``bound(...)``
and merged into each line from context variables, so call sites never pass it around.
"""

import re
from typing import cast

import structlog
from structlog.contextvars import bound_contextvars, merge_contextvars
from structlog.typing import FilteringBoundLogger

# Accept only short, plain ids from callers so a header cannot inject log content.
_CORRELATION_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")

bound = bound_contextvars


def configure_logging(json_lines: bool = True) -> None:
    """Configure structlog once per process (JSON for machines, console for humans)."""
    renderer = (
        structlog.processors.JSONRenderer() if json_lines else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            renderer,
        ]
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """Return a lazy logger tagged with ``component=name``.

    Lazy on purpose: module-level loggers are created at import time, before
    ``configure_logging`` runs, and must pick up the configuration in force when used.
    """
    return cast(FilteringBoundLogger, structlog.get_logger(component=name))


def valid_correlation_id(value: str) -> bool:
    """Whether ``value`` is safe to reuse as a correlation id."""
    return _CORRELATION_ID.fullmatch(value) is not None
