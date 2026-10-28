"""Typed accessors over database rows: right types pass, anything else is rejected."""

from datetime import UTC, datetime

import pytest

from sentinelflow.providers.storage.postgres.rows import (
    boolean,
    integer,
    json_object,
    json_records,
    json_strings,
    moment,
    optional_text,
    text,
)

ROW: dict[str, object] = {
    "s": "x",
    "n": 3,
    "none": None,
    "at": datetime(2026, 1, 1, tzinfo=UTC),
    "obj": {"a": "b"},
    "arr": ["p", "q"],
    "flag": True,
    "recs": [{"k": 1}],
}


def test_accessors_return_typed_values() -> None:
    assert (text(ROW, "s"), integer(ROW, "n"), optional_text(ROW, "none")) == ("x", 3, None)
    assert moment(ROW, "at") == datetime(2026, 1, 1, tzinfo=UTC)
    assert (json_object(ROW, "obj"), json_strings(ROW, "arr")) == ({"a": "b"}, ("p", "q"))
    assert (boolean(ROW, "flag"), json_records(ROW, "recs")) == (True, ({"k": 1},))


@pytest.mark.parametrize(
    ("accessor", "key"),
    [
        (text, "n"),
        (integer, "s"),
        (integer, "none"),
        (optional_text, "n"),
        (moment, "s"),
        (json_object, "arr"),
        (json_strings, "obj"),
        (boolean, "s"),
        (json_records, "arr"),
    ],
)
def test_wrong_column_type_is_rejected(accessor: object, key: str) -> None:
    assert callable(accessor)
    with pytest.raises(TypeError, match=key):
        accessor(ROW, key)


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(TypeError, match="at"):
        moment({"at": datetime(2026, 1, 1)}, "at")  # noqa: DTZ001 -- the case under test


def test_json_object_values_must_be_strings() -> None:
    with pytest.raises(TypeError, match="obj"):
        json_object({"obj": {"a": 1}}, "obj")


def test_bool_is_not_an_integer() -> None:
    with pytest.raises(TypeError, match="b"):
        integer({"b": True}, "b")
