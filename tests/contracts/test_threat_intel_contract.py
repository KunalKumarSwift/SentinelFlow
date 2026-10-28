"""Contract every ThreatIntelProvider implementation must satisfy."""

from collections.abc import Callable, Iterable

import pytest

from sentinelflow.contracts.threat_intel import ThreatIntelProvider
from sentinelflow.domain.enrichment import IpReputation
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from tests.fakes.fake_intel import FakeThreatIntel

Factory = Callable[[Iterable[IpReputation]], ThreatIntelProvider]
IMPLEMENTATIONS: list[Factory] = [MockThreatIntel, FakeThreatIntel]
BAD = IpReputation(ip="203.0.113.9", score=95, categories=("brute-force",))


@pytest.fixture(params=IMPLEMENTATIONS, ids=lambda f: f.__name__)
def provider(request: pytest.FixtureRequest) -> ThreatIntelProvider:
    factory: Factory = request.param
    return factory([BAD])


def test_known_ip_returns_its_reputation(provider: ThreatIntelProvider) -> None:
    assert provider.ip_reputation("203.0.113.9") == BAD


def test_unknown_ip_returns_none(provider: ThreatIntelProvider) -> None:
    assert provider.ip_reputation("198.51.100.1") is None
