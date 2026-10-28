"""Severity scale for incidents.

An ``IntEnum`` so severities compare and sort naturally (``HIGH > MEDIUM``) and
can be stored as small integers.
"""

from enum import IntEnum


class Severity(IntEnum):
    """How urgently an incident needs attention, from INFO to CRITICAL."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __str__(self) -> str:
        """Return the lowercase name, e.g. ``"high"``."""
        return self.name.lower()
