"""Time source abstraction.

Business logic never calls ``datetime.now()`` directly; it receives a ``Clock``.
This keeps time-dependent rules (dedup windows, approval expiry) deterministic in tests.
"""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Provides the current time."""

    def now(self) -> datetime:
        """Return the current time as a timezone-aware UTC datetime."""
        ...


class SystemClock:
    """Clock backed by the operating system time."""

    def now(self) -> datetime:
        """Return the current time as a timezone-aware UTC datetime."""
        return datetime.now(UTC)
