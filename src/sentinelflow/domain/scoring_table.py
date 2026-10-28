"""Base severity per detection rule and the networks treated as internal.

Data, not logic: changing how serious a rule is should be a one-line review.
"""

from collections.abc import Mapping
from ipaddress import ip_network
from types import MappingProxyType

from sentinelflow.domain.severity import Severity

RULE_BASE_SEVERITY: Mapping[str, Severity] = MappingProxyType(
    {
        "brute_force_success": Severity.MEDIUM,
        "impossible_travel": Severity.MEDIUM,
        "access_key_anomaly": Severity.HIGH,
        "phishing_click": Severity.MEDIUM,
        "suspicious_process": Severity.HIGH,
        "large_download": Severity.HIGH,
        "dormant_account": Severity.LOW,
        "over_privileged_account": Severity.LOW,
    }
)

# Explicit list: ipaddress.is_private also covers documentation and reserved ranges,
# which would wrongly lower the severity of attacks from those addresses.
INTERNAL_NETWORKS = tuple(
    ip_network(cidr)
    for cidr in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)
