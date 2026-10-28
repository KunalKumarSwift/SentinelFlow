"""Fixed-window arithmetic shared by every rate limiter."""

import math
from datetime import datetime, timedelta


def window_index(now: datetime, window: timedelta) -> int:
    """Return the number of the fixed window that contains ``now``."""
    return int(now.timestamp() * 1000) // _ms(window)


def seconds_left(now: datetime, window: timedelta) -> int:
    """Return whole seconds (at least 1) until the window containing ``now`` ends."""
    elapsed = int(now.timestamp() * 1000) % _ms(window)
    return max(1, math.ceil((_ms(window) - elapsed) / 1000))


def _ms(window: timedelta) -> int:
    return int(window.total_seconds() * 1000)
