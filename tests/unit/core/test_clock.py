"""Tests for the clock abstraction and its test fake."""

from datetime import UTC, datetime, timedelta

from sentinelflow.core.clock import Clock, SystemClock
from tests.fakes.fake_clock import FakeClock

START = datetime(2026, 1, 1, tzinfo=UTC)


def test_system_clock_returns_timezone_aware_utc() -> None:
    assert SystemClock().now().tzinfo is UTC


def test_fake_clock_starts_at_given_time() -> None:
    assert FakeClock(START).now() == START


def test_fake_clock_advances_by_delta() -> None:
    clock = FakeClock(START)
    clock.advance(timedelta(minutes=5))
    assert clock.now() == START + timedelta(minutes=5)


def test_both_clocks_satisfy_protocol() -> None:
    clocks: list[Clock] = [SystemClock(), FakeClock(START)]
    assert all(isinstance(c.now(), datetime) for c in clocks)
