"""Demo directory accounts for the access review: two of them should be flagged."""

from datetime import datetime, timedelta

from sentinelflow.domain.access_review import Account


def demo_accounts(tenant_id: str, now: datetime) -> tuple[Account, ...]:
    """Return accounts relative to ``now``: ``bob`` is dormant, ``dave`` over-privileged."""
    day = timedelta(days=1)
    return (
        Account("alice", tenant_id, frozenset({"soc-analyst-l1"}), now - day, None),
        Account("bob", tenant_id, frozenset({"soc-analyst-l2"}), now - 120 * day, None),
        Account("carol", tenant_id, frozenset({"incident-commander"}), now - day, now - 2 * day),
        Account("dave", tenant_id, frozenset({"incident-commander"}), now - day, now - 45 * day),
        Account("erin", tenant_id, frozenset({"auditor"}), now - day, None),
    )
