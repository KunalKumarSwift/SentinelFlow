"""Tests for PII pseudonymisation by role."""

import pytest

from sentinelflow.domain.alerts import Entities
from sentinelflow.security.redaction import Redactor
from tests.unit.security.policy_helpers import who

ENTITIES = Entities(user="alice", ip="203.0.113.9", email_id="msg-77")
REDACTOR = Redactor(b"k" * 32)


def test_principal_with_read_pii_sees_real_values() -> None:
    assert REDACTOR.entities_for(who("soc-analyst-l2"), ENTITIES) == ENTITIES.present()


def test_principal_without_read_pii_sees_stable_pseudonyms() -> None:
    view = REDACTOR.entities_for(who("soc-analyst-l1"), ENTITIES)
    assert view["ip"] == "203.0.113.9"
    assert view["user"].startswith("user-") and "alice" not in view["user"]
    assert view["email_id"].startswith("email_id-")
    assert view == REDACTOR.entities_for(who("executive"), ENTITIES)


def test_pseudonyms_depend_on_field_and_key() -> None:
    assert REDACTOR.pseudonym("user", "x") != REDACTOR.pseudonym("email_id", "x")
    assert REDACTOR.pseudonym("user", "x") != Redactor(b"q" * 32).pseudonym("user", "x")


def test_short_key_is_refused() -> None:
    with pytest.raises(ValueError, match="32"):
        Redactor(b"short")
