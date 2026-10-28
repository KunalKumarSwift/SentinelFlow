"""JWKS cache: keys refresh on rotation (unknown kid) and on expiry, but not on every miss."""

from datetime import timedelta

from sentinelflow.security.oidc.jwks import MIN_REFRESH, CachedJwks
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.unit.security.oidc.keys import jwks


class Source:
    """Serves whichever key set is current and counts fetches."""

    def __init__(self, *kids: str) -> None:
        self.kids, self.fetches = kids, 0

    def __call__(self) -> dict[str, object]:
        self.fetches += 1
        return jwks(*self.kids)


def test_known_key_is_served_from_the_cache() -> None:
    source = Source("k1")
    cache = CachedJwks(source, FakeClock(T0))
    assert cache.key("k1") is not None and cache.key("k1") is not None
    assert source.fetches == 1


def test_rotated_key_is_picked_up_on_first_sight() -> None:
    source, clock = Source("k1"), FakeClock(T0)
    cache = CachedJwks(source, clock)
    cache.key("k1")
    source.kids = ("k1", "k2")
    clock.advance(MIN_REFRESH)
    assert cache.key("k2") is not None


def test_unknown_keys_cannot_force_a_fetch_storm() -> None:
    source = Source("k1")
    cache = CachedJwks(source, FakeClock(T0))
    for _ in range(5):
        assert cache.key("rogue") is None
    assert source.fetches == 1


def test_keys_are_refreshed_after_the_ttl() -> None:
    source, clock = Source("k1"), FakeClock(T0)
    cache = CachedJwks(source, clock, ttl=timedelta(minutes=10))
    cache.key("k1")
    clock.advance(timedelta(minutes=10))
    cache.key("k1")
    assert source.fetches == 2
