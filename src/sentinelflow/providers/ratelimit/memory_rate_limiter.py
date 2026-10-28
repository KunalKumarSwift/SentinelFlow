"""In-process fixed-window rate limiter (single-process mode and tests)."""

from datetime import timedelta
from threading import Lock

from sentinelflow.core.clock import Clock
from sentinelflow.providers.ratelimit.window import seconds_left, window_index


class MemoryRateLimiter:
    """Counts hits per key for the current window only."""

    def __init__(self, clock: Clock) -> None:
        """Measure windows with ``clock``."""
        self._clock = clock
        self._counts: dict[str, tuple[int, int]] = {}  # key -> (window index, hits)
        self._lock = Lock()

    def hit(self, key: str, limit: int, window: timedelta) -> int | None:
        """Count a hit; return seconds to wait if ``limit`` is exceeded."""
        now = self._clock.now()
        index = window_index(now, window)
        with self._lock:
            current, hits = self._counts.get(key, (index, 0))
            hits = hits + 1 if current == index else 1
            self._counts[key] = (index, hits)
        return None if hits <= limit else seconds_left(now, window)
