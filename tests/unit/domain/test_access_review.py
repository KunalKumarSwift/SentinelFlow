"""Access-review rules: dormant accounts and unused privileged roles, as findings."""

from datetime import timedelta

from sentinelflow.domain.access_review import (
    DORMANT_AFTER,
    UNUSED_PRIVILEGE_AFTER,
    Account,
    Finding,
    review_accounts,
)
from tests.builders import T0


def _account(user: str, **changes: object) -> Account:
    base = {
        "user_id": user,
        "tenant_id": "acme",
        "roles": frozenset({"soc-analyst-l1"}),
        "last_login": T0 - timedelta(days=1),
        "last_privileged_use": None,
    }
    return Account(**{**base, **changes})  # pyright: ignore[reportArgumentType] -- test overrides


def test_active_unprivileged_account_has_no_findings() -> None:
    assert review_accounts([_account("alice")], T0) == ()


def test_account_without_login_for_90_days_is_dormant() -> None:
    old = _account("bob", last_login=T0 - DORMANT_AFTER)
    never = _account("carl", last_login=None)
    fresh = _account("dina", last_login=T0 - DORMANT_AFTER + timedelta(seconds=1))
    findings = review_accounts([old, never, fresh], T0)
    assert [(f.rule_id, f.user_id) for f in findings] == [
        ("dormant_account", "bob"),
        ("dormant_account", "carl"),
    ]


def test_privileged_role_unused_for_30_days_is_over_privileged() -> None:
    idle = _account(
        "erin",
        roles=frozenset({"incident-commander"}),
        last_privileged_use=T0 - UNUSED_PRIVILEGE_AFTER,
    )
    busy = _account(
        "finn", roles=frozenset({"platform-admin"}), last_privileged_use=T0 - timedelta(days=2)
    )
    findings = review_accounts([idle, busy], T0)
    assert findings == (
        Finding(
            "over_privileged_account",
            "erin",
            "privileged roles incident-commander unused for 30+ days",
        ),
    )


def test_dormant_account_is_reported_once_as_dormant() -> None:
    both = _account("gail", roles=frozenset({"platform-admin"}), last_login=None)
    assert [f.rule_id for f in review_accounts([both], T0)] == ["dormant_account"]


def test_findings_name_the_reason() -> None:
    [finding] = review_accounts([_account("hugo", last_login=None)], T0)
    assert finding.reason == "no login for 90+ days"
