"""Threat intel from AbuseIPDB (free tier: 1 000 checks/day).

Only non-internal addresses are looked up: internal IPs say nothing to AbuseIPDB and would
leak our network layout to a third party. An IP nobody has reported is "no intel"
(``None``), never a made-up clean score. Errors never include the API key.
"""

import ipaddress
from typing import cast

import httpx

from sentinelflow.domain.enrichment import IpReputation
from sentinelflow.domain.errors import ProviderError
from sentinelflow.domain.scoring_table import INTERNAL_NETWORKS

API_URL = "https://api.abuseipdb.com/api/v2/check"
_RETRYABLE = {429, 500, 502, 503, 504}


class AbuseIpdbThreatIntel:
    """``ThreatIntelProvider`` backed by the AbuseIPDB v2 ``check`` endpoint."""

    def __init__(self, api_key: str, transport: httpx.BaseTransport | None = None) -> None:
        """Authenticate with ``api_key``; ``transport`` lets tests replace the network."""
        headers = {"Key": api_key, "Accept": "application/json"}
        self._client = httpx.Client(headers=headers, transport=transport, timeout=5)

    def ip_reputation(self, ip: str) -> IpReputation | None:
        """Return AbuseIPDB's view of a public ``ip``; ``None`` if internal or unreported.

        Raises:
            ProviderError: If AbuseIPDB fails (429/5xx and network errors are retryable).
        """
        if not _is_public(ip):
            return None
        data = self._check(ip)
        score, reports = data.get("abuseConfidenceScore"), data.get("totalReports")
        if not isinstance(score, int) or not isinstance(reports, int):
            raise ProviderError("AbuseIPDB answer missing score", retryable=False)
        if reports == 0:
            return None
        country = data.get("countryCode")
        return IpReputation(
            ip, score, ("abuseipdb",), country if isinstance(country, str) else None
        )

    def _check(self, ip: str) -> dict[str, object]:
        try:
            response = self._client.get(API_URL, params={"ipAddress": ip, "maxAgeInDays": 90})
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"AbuseIPDB unreachable: {type(exc).__name__}", retryable=True
            ) from exc
        if response.is_error:
            status = response.status_code
            raise ProviderError(f"AbuseIPDB returned {status}", retryable=status in _RETRYABLE)
        body: object = response.json()
        data = cast(dict[str, object], body).get("data") if isinstance(body, dict) else None
        if not isinstance(data, dict):
            raise ProviderError("AbuseIPDB answer has no data", retryable=False)
        return cast(dict[str, object], data)


def _is_public(ip: str) -> bool:
    # Same definition of "internal" as severity scoring, so both agree on every address.
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not any(address in network for network in INTERNAL_NETWORKS)
