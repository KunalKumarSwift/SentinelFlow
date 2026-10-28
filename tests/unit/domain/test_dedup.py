"""Tests for alert fingerprinting and the duplicate-window rule."""

from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from sentinelflow.domain.dedup import DEFAULT_DEDUP_WINDOW, fingerprint_alert, is_duplicate
from tests.builders import T0, an_alert, some_entities


def test_fingerprint_is_sha256_hex() -> None:
    fingerprint = fingerprint_alert(an_alert())
    assert len(fingerprint) == 64
    assert set(fingerprint) <= set("0123456789abcdef")


@given(title=st.text(min_size=1), minutes=st.integers(0, 10_000))
def test_fingerprint_ignores_id_title_time_and_raw(title: str, minutes: int) -> None:
    other = an_alert(
        id="alt-9999",
        title=title,
        observed_at=T0 + timedelta(minutes=minutes),
        raw={"note": title},
    )
    assert fingerprint_alert(other) == fingerprint_alert(an_alert())


@pytest.mark.parametrize(
    "changes",
    [
        {"tenant_id": "globex"},
        {"rule_id": "impossible_travel"},
        {"entities": some_entities(user="bob")},
        {"entities": some_entities(host="ws-17")},
    ],
)
def test_fingerprint_changes_with_tenant_rule_or_entities(changes: dict[str, object]) -> None:
    assert fingerprint_alert(an_alert(**changes)) != fingerprint_alert(an_alert())


def test_fingerprint_distinguishes_which_entity_holds_a_value() -> None:
    as_user = an_alert(entities=some_entities(user="x", ip=None))
    as_host = an_alert(entities=some_entities(user=None, ip=None, host="x"))
    assert fingerprint_alert(as_user) != fingerprint_alert(as_host)


def test_first_sighting_is_not_a_duplicate() -> None:
    assert is_duplicate(last_seen=None, observed_at=T0) is False


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (timedelta(minutes=1), True),
        (DEFAULT_DEDUP_WINDOW, True),
        (DEFAULT_DEDUP_WINDOW + timedelta(seconds=1), False),
        (-timedelta(minutes=5), True),
    ],
)
def test_duplicate_only_within_window(offset: timedelta, expected: bool) -> None:
    assert is_duplicate(last_seen=T0, observed_at=T0 + offset) is expected


def test_custom_window_is_respected() -> None:
    later = T0 + timedelta(minutes=20)
    assert is_duplicate(last_seen=T0, observed_at=later, window=timedelta(hours=1)) is True
