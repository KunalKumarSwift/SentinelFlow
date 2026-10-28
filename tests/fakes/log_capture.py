"""Capture structlog events, including context-bound fields, for assertions."""

from collections.abc import Generator, MutableMapping
from contextlib import contextmanager

import structlog
from structlog.contextvars import merge_contextvars
from structlog.typing import EventDict, WrappedLogger


class Captured:
    """Records every event dict that reaches the end of the processor chain."""

    def __init__(self) -> None:
        self.events: list[EventDict] = []

    def __call__(
        self, _logger: WrappedLogger, _method: str, event: MutableMapping[str, object]
    ) -> EventDict:
        self.events.append(dict(event))
        raise structlog.DropEvent

    def named(self, name: str) -> list[EventDict]:
        """Return the captured events whose message is ``name``."""
        return [e for e in self.events if e.get("event") == name]


@contextmanager
def capture_logs() -> Generator[Captured]:
    """Route structlog into a ``Captured`` for the duration of the block."""
    captured = Captured()
    structlog.configure(processors=[merge_contextvars, captured])
    try:
        yield captured
    finally:
        structlog.reset_defaults()
        structlog.contextvars.clear_contextvars()
