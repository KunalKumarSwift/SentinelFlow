"""Tests for building an investigation timeline from raw events."""

from datetime import timedelta

from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.domain.timeline import build_timeline
from tests.builders import T0


def _event(n: int, kind: str, minutes: int) -> SecurityEvent:
    return SecurityEvent(
        f"evt-{n}", "acme", T0 + timedelta(minutes=minutes), kind, Entities(user="alice")
    )


def test_consecutive_repeats_collapse_into_one_entry() -> None:
    events = [
        _event(3, "login_succeeded", 9),
        _event(1, "login_failed", 0),
        _event(2, "login_failed", 1),
    ]
    timeline = build_timeline(events)
    assert [(e.summary, e.first_event_id, e.count) for e in timeline] == [
        ("login_failed x2 (user=alice)", "evt-1", 2),
        ("login_succeeded (user=alice)", "evt-3", 1),
    ]
    assert (timeline[0].start, timeline[0].end) == (T0, T0 + timedelta(minutes=1))


def test_empty_events_give_empty_timeline() -> None:
    assert build_timeline([]) == ()
