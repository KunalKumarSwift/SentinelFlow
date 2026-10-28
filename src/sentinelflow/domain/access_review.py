"""Access-review rules: dormant accounts and privileged roles nobody uses.

Pure functions over account snapshots; the scheduled access-review workflow turns each
finding into a LOW-severity incident so it gets the normal triage, audit and report path.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

DORMANT_AFTER = timedelta(days=90)
UNUSED_PRIVILEGE_AFTER = timedelta(days=30)
PRIVILEGED_ROLES = frozenset({"incident-commander", "platform-admin", "security-engineer"})


@dataclass(frozen=True, slots=True)
class Account:
    """A directory account with the activity facts the review needs."""

    user_id: str
    tenant_id: str
    roles: frozenset[str]
    last_login: datetime | None
    last_privileged_use: datetime | None


@dataclass(frozen=True, slots=True)
class Finding:
    """One review result; ``rule_id`` is a detection rule with a base severity."""

    rule_id: str
    user_id: str
    reason: str


def review_accounts(accounts: Iterable[Account], now: datetime) -> tuple[Finding, ...]:
    """Return findings in account order; a dormant account is reported only as dormant."""
    findings = (_dormant(a, now) or _over_privileged(a, now) for a in accounts)
    return tuple(f for f in findings if f is not None)


def _dormant(account: Account, now: datetime) -> Finding | None:
    if account.last_login is not None and now - account.last_login < DORMANT_AFTER:
        return None
    return Finding("dormant_account", account.user_id, "no login for 90+ days")


def _over_privileged(account: Account, now: datetime) -> Finding | None:
    privileged = sorted(account.roles & PRIVILEGED_ROLES)
    used = account.last_privileged_use
    if not privileged or (used is not None and now - used < UNUSED_PRIVILEGE_AFTER):
        return None
    roles = ", ".join(privileged)
    return Finding(
        "over_privileged_account", account.user_id, f"privileged roles {roles} unused for 30+ days"
    )
