"""Tests for per-rule containment playbooks."""

import pytest

from sentinelflow.domain.actions import ActionKind as K
from sentinelflow.domain.playbooks import playbook_for
from sentinelflow.domain.scoring_table import RULE_BASE_SEVERITY


@pytest.mark.parametrize(
    ("rule_id", "actions"),
    [
        ("brute_force_success", (K.DISABLE_USER, K.BLOCK_IP)),
        ("impossible_travel", (K.FORCE_MFA_RESET,)),
        ("access_key_anomaly", (K.REVOKE_ACCESS_KEY,)),
        ("phishing_click", (K.PURGE_EMAIL, K.RESET_PASSWORD)),
        ("suspicious_process", (K.ISOLATE_HOST,)),
        ("large_download", ()),
    ],
)
def test_playbook(rule_id: str, actions: tuple[K, ...]) -> None:
    assert playbook_for(rule_id) == actions


def test_every_known_rule_has_a_playbook_entry() -> None:
    assert all(isinstance(playbook_for(rule), tuple) for rule in RULE_BASE_SEVERITY)


def test_unknown_rule_has_no_actions() -> None:
    assert playbook_for("mystery") == ()
