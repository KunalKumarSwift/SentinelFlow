"""RBAC tests: every (role, permission) pair is checked against the spec."""

from itertools import product

import pytest

from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.security.permissions import Permission
from sentinelflow.security.rbac import has_permission, permissions_of
from sentinelflow.security.roles import ROLE_PERMISSIONS
from tests.unit.security.rbac_spec import EXPECTED

HUMAN_ROLES = set(EXPECTED) - {"alert-source", "orchestrator"}


def _principal(*roles: str) -> Principal:
    return Principal("u-1", "acme", "soc-emea", frozenset(roles), PrincipalKind.USER)


def test_code_and_spec_define_the_same_roles() -> None:
    assert set(ROLE_PERMISSIONS) == set(EXPECTED)


@pytest.mark.parametrize(("role", "permission"), list(product(EXPECTED, Permission)))
def test_rbac_matrix(role: str, permission: Permission) -> None:
    expected = permission in EXPECTED[role]
    assert has_permission(_principal(role), permission) is expected


def test_no_human_role_can_execute_actions() -> None:
    assert not any(Permission.ACTION_EXECUTE in ROLE_PERMISSIONS[r] for r in HUMAN_ROLES)


def test_unknown_role_grants_nothing() -> None:
    assert permissions_of(_principal("god-mode")) == frozenset()


def test_multiple_roles_combine() -> None:
    granted = permissions_of(_principal("auditor", "executive"))
    assert {Permission.AUDIT_READ, Permission.INCIDENT_READ_ALL} <= granted
