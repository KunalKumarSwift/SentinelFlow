"""Controllable clock for tests."""

from datetime import datetime, timedelta


class FakeClock:
    """Clock that only moves when the test advances it."""

    def __init__(self, start: datetime) -> None:
        """Create a clock frozen at ``start``."""
        self._now = start

    def now(self) -> datetime:
        """Return the frozen current time."""
        return self._now

    def advance(self, delta: timedelta) -> None:
        """Move the clock forward by ``delta``."""
        self._now += delta
