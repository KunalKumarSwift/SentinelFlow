"""Tests for the action catalogue and approval requirements."""

import pytest

from sentinelflow.domain.actions import (
    ActionKind,
    Impact,
    ProposedAction,
    approval_requirement,
    parse_action_kind,
    target_of,
    targets_user,
)
from sentinelflow.domain.errors import InvalidValueError, UnknownActionError
from sentinelflow.domain.severity import Severity
from tests.builders import some_entities

K = ActionKind


@pytest.mark.parametrize(
    ("kind", "impact"),
    [
        (K.BLOCK_IP, Impact.LOW),
        (K.FORCE_MFA_RESET, Impact.LOW),
        (K.PURGE_EMAIL, Impact.MEDIUM),
        (K.RESET_PASSWORD, Impact.MEDIUM),
        (K.DISABLE_USER, Impact.HIGH),
        (K.REVOKE_ACCESS_KEY, Impact.HIGH),
        (K.ISOLATE_HOST, Impact.HIGH),
    ],
)
def test_every_action_has_its_impact(kind: ActionKind, impact: Impact) -> None:
    assert ProposedAction("act-1", "inc-1", kind, "x", "why", "svc").impact is impact


@pytest.mark.parametrize(
    ("kind", "severity", "role", "count"),
    [
        (K.BLOCK_IP, Severity.CRITICAL, "soc-analyst-l2", 1),
        (K.RESET_PASSWORD, Severity.HIGH, "soc-analyst-l2", 1),
        (K.DISABLE_USER, Severity.HIGH, "incident-commander", 1),
        (K.DISABLE_USER, Severity.CRITICAL, "incident-commander", 2),
        (K.REVOKE_ACCESS_KEY, Severity.CRITICAL, "incident-commander", 2),
    ],
)
def test_approval_requirement(kind: ActionKind, severity: Severity, role: str, count: int) -> None:
    requirement = approval_requirement(kind, severity)
    assert (requirement.role, requirement.count) == (role, count)


@pytest.mark.parametrize(
    ("kind", "expected"),
    [(K.DISABLE_USER, "alice"), (K.BLOCK_IP, "203.0.113.9"), (K.ISOLATE_HOST, None)],
)
def test_target_comes_from_matching_entity(kind: ActionKind, expected: str | None) -> None:
    assert target_of(kind, some_entities()) == expected


def test_parse_accepts_catalogue_values() -> None:
    assert parse_action_kind("disable_user") is K.DISABLE_USER


@pytest.mark.parametrize("value", ["drop_database", "DISABLE_USER", ""])
def test_parse_rejects_anything_else(value: str) -> None:
    with pytest.raises(UnknownActionError):
        parse_action_kind(value)


def test_proposed_action_needs_target_and_reason() -> None:
    with pytest.raises(InvalidValueError, match="target"):
        ProposedAction("act-1", "inc-1", K.BLOCK_IP, " ", "why", "svc")


def test_only_user_actions_target_users() -> None:
    assert [k for k in K if targets_user(k)] == [
        K.FORCE_MFA_RESET,
        K.RESET_PASSWORD,
        K.DISABLE_USER,
    ]
