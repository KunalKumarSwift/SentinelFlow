"""Choose the threat-intel provider from settings. Switch logic only."""

from collections.abc import Iterable

from sentinelflow.contracts.threat_intel import ThreatIntelProvider
from sentinelflow.core.config import Settings
from sentinelflow.domain.enrichment import IpReputation


def make_threat_intel(settings: Settings, seeded: Iterable[IpReputation]) -> ThreatIntelProvider:
    """Return AbuseIPDB when configured, else the mock serving ``seeded`` (demo data)."""
    if settings.intel_backend == "abuseipdb" and settings.abuseipdb_api_key is not None:
        from sentinelflow.providers.intel.abuseipdb_intel import AbuseIpdbThreatIntel

        return AbuseIpdbThreatIntel(settings.abuseipdb_api_key.get_secret_value())
    from sentinelflow.providers.intel.mock_intel import MockThreatIntel

    return MockThreatIntel(seeded)
