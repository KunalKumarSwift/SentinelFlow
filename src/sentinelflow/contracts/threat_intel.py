"""Interface for looking up the reputation of network indicators."""

from typing import Protocol

from sentinelflow.domain.enrichment import IpReputation


class ThreatIntelProvider(Protocol):
    """Answers "how dangerous is this indicator?" from a threat-intel source."""

    def ip_reputation(self, ip: str) -> IpReputation | None:
        """Return the reputation of ``ip``, or ``None`` if the source knows nothing about it.

        Raises:
            ProviderError: If the source cannot be reached (real providers only).
        """
        ...
