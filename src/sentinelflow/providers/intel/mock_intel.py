"""Threat intel served from in-memory data, e.g. a simulator scenario's seed data.

Used when ``INTEL_BACKEND=mock`` so the whole platform runs offline and for free.
"""

from collections.abc import Iterable

from sentinelflow.domain.enrichment import IpReputation


class MockThreatIntel:
    """Answers reputation lookups from a fixed set of known indicators."""

    def __init__(self, reputations: Iterable[IpReputation]) -> None:
        """Index ``reputations`` by IP address."""
        self._by_ip = {rep.ip: rep for rep in reputations}

    def ip_reputation(self, ip: str) -> IpReputation | None:
        """Return the stored reputation of ``ip``, or ``None`` if unknown."""
        return self._by_ip.get(ip)
