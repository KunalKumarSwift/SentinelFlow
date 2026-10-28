"""Predictable id factory for tests."""

from collections import Counter

from sentinelflow.core.ids import validate_prefix


class SequentialIdFactory:
    """Creates ids like ``inc-0001``, counting separately per prefix."""

    def __init__(self) -> None:
        """Start every prefix counter at zero."""
        self._counters: Counter[str] = Counter()

    def new_id(self, prefix: str) -> str:
        """Return the next sequential id for ``prefix``."""
        validate_prefix(prefix)
        self._counters[prefix] += 1
        return f"{prefix}-{self._counters[prefix]:04d}"
