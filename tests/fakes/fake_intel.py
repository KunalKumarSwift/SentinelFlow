"""Recording threat-intel fake for tests."""

from collections.abc import Iterable

from sentinelflow.domain.enrichment import IpReputation


class FakeThreatIntel:
    """In-memory threat intel that remembers which IPs were looked up."""

    def __init__(self, reputations: Iterable[IpReputation]) -> None:
        """Serve ``reputations``; everything else is unknown."""
        self._by_ip = {rep.ip: rep for rep in reputations}
        self.lookups: list[str] = []

    def ip_reputation(self, ip: str) -> IpReputation | None:
        """Record the lookup and return the stored reputation, if any."""
        self.lookups.append(ip)
        return self._by_ip.get(ip)
