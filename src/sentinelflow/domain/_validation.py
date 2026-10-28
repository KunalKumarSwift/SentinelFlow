"""Invariant checks shared by domain value objects."""

from datetime import datetime

from sentinelflow.domain.errors import InvalidValueError


def require_text(value: str, field: str) -> None:
    """Raise ``InvalidValueError`` if ``value`` is empty or only whitespace.

    Args:
        value: The text to check.
        field: Field name used in the error message.

    Raises:
        InvalidValueError: If the text is blank.
    """
    if not value.strip():
        raise InvalidValueError(f"{field} must not be blank")


def require_aware(value: datetime, field: str) -> None:
    """Raise ``InvalidValueError`` if ``value`` has no timezone.

    Args:
        value: The timestamp to check.
        field: Field name used in the error message.

    Raises:
        InvalidValueError: If the timestamp is naive.

    Note:
        Naive timestamps are ambiguous across regions and break dedup windows.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidValueError(f"{field} must be timezone-aware")
