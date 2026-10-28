"""Mock intel by default; AbuseIPDB when configured with a key."""

from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.intel_facade import make_threat_intel
from sentinelflow.providers.intel.abuseipdb_intel import AbuseIpdbThreatIntel
from sentinelflow.providers.intel.mock_intel import MockThreatIntel

SECRET = SecretStr("s" * 32)


def test_default_is_the_seeded_mock() -> None:
    assert isinstance(make_threat_intel(Settings(jwt_secret=SECRET), []), MockThreatIntel)  # type: ignore[call-arg]


def test_abuseipdb_is_selected_with_a_key() -> None:
    settings = Settings(  # type: ignore[call-arg]
        jwt_secret=SECRET, intel_backend="abuseipdb", abuseipdb_api_key=SecretStr("k" * 80)
    )
    assert isinstance(make_threat_intel(settings, []), AbuseIpdbThreatIntel)
