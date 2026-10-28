"""Alert fingerprinting and the duplicate-window rule.

Two alerts are "the same" when tenant, detection rule and entities match. Title,
timestamps and raw fields are excluded because they vary between repeats of one
attack. The fingerprint hashes canonical JSON so values containing separators
cannot collide (``user="a|b"`` vs. two fields ``"a"`` and ``"b"``).
"""

import hashlib
import json
from datetime import datetime, timedelta

from sentinelflow.domain.alerts import Alert

DEFAULT_DEDUP_WINDOW = timedelta(minutes=15)


def fingerprint_alert(alert: Alert) -> str:
    """Return a stable SHA-256 hex digest identifying repeats of the same alert.

    Args:
        alert: The alert to fingerprint.

    Returns:
        64 lowercase hex characters.
    """
    identity = [alert.tenant_id, alert.rule_id, sorted(alert.entities.present().items())]
    canonical = json.dumps(identity, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def is_duplicate(
    last_seen: datetime | None,
    observed_at: datetime,
    window: timedelta = DEFAULT_DEDUP_WINDOW,
) -> bool:
    """Decide whether an alert repeats one already seen with the same fingerprint.

    Args:
        last_seen: When the fingerprint was last seen, or ``None`` if never.
        observed_at: When the new alert was observed.
        window: Maximum distance in time for the two to count as duplicates.

    Returns:
        ``True`` if the alerts are within ``window`` of each other, in either order.

    Note:
        The distance is absolute because sources may deliver alerts out of order.
    """
    if last_seen is None:
        return False
    return abs(observed_at - last_seen) <= window
