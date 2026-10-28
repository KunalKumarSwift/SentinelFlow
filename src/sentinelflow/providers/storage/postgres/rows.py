"""Typed accessors for database rows and decoded JSON.

The driver returns untyped values; these helpers check each one at the boundary so the
rest of the code stays fully typed and a schema drift fails loudly instead of silently.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import cast

Row = Mapping[str, object]


def text(row: Row, key: str) -> str:
    """Return ``row[key]`` as a string."""
    return _expect(row, key, str)


def optional_text(row: Row, key: str) -> str | None:
    """Return ``row[key]`` as a string, or ``None`` for SQL null."""
    return None if row[key] is None else text(row, key)


def integer(row: Row, key: str) -> int:
    """Return ``row[key]`` as an integer (booleans are rejected)."""
    if isinstance(row[key], bool):
        raise TypeError(f"column {key!r}: expected int, got bool")
    return _expect(row, key, int)


def boolean(row: Row, key: str) -> bool:
    """Return ``row[key]`` as a boolean."""
    return _expect(row, key, bool)


def moment(row: Row, key: str) -> datetime:
    """Return ``row[key]`` as a timezone-aware datetime."""
    value = _expect(row, key, datetime)
    if value.tzinfo is None:
        raise TypeError(f"column {key!r}: naive datetime")
    return value


def json_object(row: Row, key: str) -> dict[str, str]:
    """Return ``row[key]`` as a JSON object whose values are all strings."""
    value = json_record(row, key)
    if not all(isinstance(v, str) for v in value.values()):
        raise TypeError(f"column {key!r}: expected string values")
    return {k: str(v) for k, v in value.items()}


def json_record(row: Row, key: str) -> Row:
    """Return ``row[key]`` as a JSON object with values of any type."""
    return cast(Row, _expect(row, key, dict))


def json_strings(row: Row, key: str) -> tuple[str, ...]:
    """Return ``row[key]`` as a JSON array of strings."""
    return tuple(text({key: item}, key) for item in _json_list(row, key))


def json_records(row: Row, key: str) -> tuple[Row, ...]:
    """Return ``row[key]`` as a JSON array of objects."""
    return tuple(json_record({key: item}, key) for item in _json_list(row, key))


def _json_list(row: Row, key: str) -> list[object]:
    return cast(list[object], _expect(row, key, list))


def _expect[T](row: Row, key: str, kind: type[T]) -> T:
    value = row[key]
    if not isinstance(value, kind):
        raise TypeError(f"column {key!r}: expected {kind.__name__}, got {type(value).__name__}")
    return value
