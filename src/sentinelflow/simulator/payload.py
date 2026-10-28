"""Serialise a domain alert into the body ``POST /v1/alerts`` expects.

The tenant is deliberately absent: the API takes it from the caller's token.
"""

from sentinelflow.domain.alerts import Alert


def alert_payload(alert: Alert) -> dict[str, object]:
    """Return the JSON-ready request body for ``alert``."""
    return {
        "source": alert.source,
        "rule_id": alert.rule_id,
        "title": alert.title,
        "observed_at": alert.observed_at.isoformat(),
        "entities": alert.entities.present(),
        "raw": dict(alert.raw),
    }
