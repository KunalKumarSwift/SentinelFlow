"""Interface of a shared request counter used for per-tenant rate limiting."""

from datetime import timedelta
from typing import Protocol


class RateLimiter(Protocol):
    """Fixed-window counter: at most ``limit`` hits per ``key`` in each ``window``."""

    def hit(self, key: str, limit: int, window: timedelta) -> int | None:
        """Count one hit for ``key``.

        Returns:
            ``None`` if the hit is within the limit, otherwise the whole seconds (>= 1)
            until the current window ends.
        """
        ...
