"""In-process daily token budget (single-process mode and tests)."""

from datetime import date
from threading import Lock

from sentinelflow.core.clock import Clock


class MemoryTokenBudget:
    """Keeps today's spend per tenant; earlier days are forgotten as they pass."""

    def __init__(self, clock: Clock) -> None:
        """Decide "today" (UTC) with ``clock``."""
        self._clock = clock
        self._spent: dict[tuple[str, date], int] = {}
        self._lock = Lock()

    def try_spend(self, tenant_id: str, tokens: int, daily_limit: int) -> bool:
        """Reserve ``tokens`` if the tenant stays within ``daily_limit`` today."""
        key = (tenant_id, self._clock.now().date())
        with self._lock:
            spent = self._spent.get(key, 0)
            if spent + tokens > daily_limit:
                return False
            self._spent = {k: v for k, v in self._spent.items() if k[1] == key[1]}
            self._spent[key] = spent + tokens
            return True
