"""AbuseIPDB lookups: score mapping, 'no intel', error classification, and privacy."""

import httpx
import pytest

from sentinelflow.domain.enrichment import IpReputation
from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.intel.abuseipdb_intel import AbuseIpdbThreatIntel

IP = "203.0.113.9"


def _intel(
    response: httpx.Response, seen: list[httpx.Request] | None = None
) -> AbuseIpdbThreatIntel:
    def handle(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return response

    return AbuseIpdbThreatIntel("k" * 80, transport=httpx.MockTransport(handle))


def _data(score: int, reports: int) -> dict[str, object]:
    return {
        "data": {
            "ipAddress": IP,
            "abuseConfidenceScore": score,
            "totalReports": reports,
            "countryCode": "NL",
        }
    }


def test_reported_ip_maps_to_a_reputation_and_sends_the_key() -> None:
    seen: list[httpx.Request] = []
    rep = _intel(httpx.Response(200, json=_data(97, 31)), seen).ip_reputation(IP)
    assert rep == IpReputation(IP, 97, ("abuseipdb",), "NL")
    assert seen[0].headers["Key"] == "k" * 80
    assert seen[0].url.params["ipAddress"] == IP


def test_never_reported_ip_is_no_intel() -> None:
    assert _intel(httpx.Response(200, json=_data(0, 0))).ip_reputation(IP) is None


@pytest.mark.parametrize("ip", ["10.0.0.5", "192.168.1.1", "127.0.0.1", "not-an-ip"])
def test_internal_or_invalid_addresses_are_never_sent_out(ip: str) -> None:
    seen: list[httpx.Request] = []
    assert _intel(httpx.Response(200, json=_data(90, 5)), seen).ip_reputation(ip) is None
    assert seen == []


@pytest.mark.parametrize(
    ("response", "retryable"),
    [
        (httpx.Response(429), True),
        (httpx.Response(503), True),
        (httpx.Response(401), False),
        (httpx.Response(200, json={"unexpected": True}), False),
    ],
)
def test_failures_are_provider_errors(response: httpx.Response, retryable: bool) -> None:
    with pytest.raises(ProviderError) as caught:
        _intel(response).ip_reputation(IP)
    assert caught.value.retryable is retryable
    assert "k" * 80 not in str(caught.value)


def test_unreachable_service_is_retryable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    intel = AbuseIpdbThreatIntel("k" * 80, transport=httpx.MockTransport(refuse))
    with pytest.raises(ProviderError) as caught:
        intel.ip_reputation(IP)
    assert caught.value.retryable


def test_answer_without_a_score_is_rejected() -> None:
    with pytest.raises(ProviderError, match="score"):
        _intel(httpx.Response(200, json={"data": {"totalReports": 3}})).ip_reputation(IP)
