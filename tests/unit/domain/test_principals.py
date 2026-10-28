"""Tests for the Principal value object."""

import pytest

from sentinelflow.domain.errors import InvalidValueError
from sentinelflow.domain.principals import Principal, PrincipalKind


def test_principal_holds_roles_as_frozenset() -> None:
    principal = Principal("u-alice", "acme", "soc-emea", frozenset({"soc-analyst-l1"}))
    assert principal.roles == frozenset({"soc-analyst-l1"})
    assert principal.kind is PrincipalKind.USER


@pytest.mark.parametrize("field", ["subject", "tenant_id"])
def test_blank_identity_is_rejected(field: str) -> None:
    values = {"subject": "u-alice", "tenant_id": "acme", field: " "}
    with pytest.raises(InvalidValueError, match=field):
        Principal(values["subject"], values["tenant_id"], "soc-emea", frozenset())
