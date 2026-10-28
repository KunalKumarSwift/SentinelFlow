"""Deterministic severity scoring for incidents.

Severity is computed by rules, never by the LLM, so it is explainable and cannot be
talked down by text inside an alert. Each signal moves severity by one level:

* +1 if the source IP is known malicious
* +1 if the user is privileged
* -1 if the IP is internal and the user is not privileged
"""

import ipaddress

from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.enrichment import Enrichment
from sentinelflow.domain.errors import UnknownRuleError
from sentinelflow.domain.scoring_table import INTERNAL_NETWORKS, RULE_BASE_SEVERITY
from sentinelflow.domain.severity import Severity


def score_severity(rule_id: str, entities: Entities, enrichment: Enrichment) -> Severity:
    """Return the incident severity for a rule, adjusted by enrichment signals.

    Args:
        rule_id: Detection rule that raised the alert, e.g. ``"brute_force_success"``.
        entities: Entities named by the incident; ``ip`` decides internal vs. external.
        enrichment: Threat-intel and user context gathered during triage.

    Returns:
        The adjusted severity, clamped to the INFO..CRITICAL range.

    Raises:
        UnknownRuleError: If ``rule_id`` has no base severity.
    """
    base = RULE_BASE_SEVERITY.get(rule_id)
    if base is None:
        raise UnknownRuleError(f"no base severity for rule {rule_id!r}")
    level = base + _adjustment(entities, enrichment)
    return Severity(min(max(level, Severity.INFO), Severity.CRITICAL))


def _adjustment(entities: Entities, enrichment: Enrichment) -> int:
    rep, user = enrichment.ip_reputation, enrichment.user
    privileged = user is not None and user.is_privileged
    malicious = rep is not None and rep.is_malicious
    internal = _is_internal(entities.ip)
    return int(malicious) + int(privileged) - int(internal and not privileged)


def _is_internal(ip: str | None) -> bool:
    if ip is None:
        return False
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        # Unparseable addresses get no benefit of the doubt.
        return False
    return any(address in network for network in INTERNAL_NETWORKS)
