"""Tests for the workflow registry and start authorisation."""

import pytest

from sentinelflow.domain.errors import PolicyDeniedError, UnknownWorkflowError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission
from sentinelflow.workflows.registry import DEFAULT_REGISTRY


def _principal(role: str) -> Principal:
    return Principal("u-1", "acme", "soc-emea", frozenset({role}))


def test_lists_registered_workflows_by_name() -> None:
    assert [d.name for d in DEFAULT_REGISTRY.list()] == ["triage"]


def test_triage_scope_is_read_only() -> None:
    scope = DEFAULT_REGISTRY.get("triage").max_scope
    assert scope == {Permission.INTEL_LOOKUP, Permission.IDENTITY_READ}


def test_unknown_workflow_is_rejected() -> None:
    with pytest.raises(UnknownWorkflowError, match="exfiltrate"):
        DEFAULT_REGISTRY.get("exfiltrate")


@pytest.mark.parametrize("role", ["soc-analyst-l1", "soc-analyst-l2", "orchestrator"])
def test_permitted_roles_may_start_triage(role: str) -> None:
    assert DEFAULT_REGISTRY.authorize_start(_principal(role), "triage").name == "triage"


@pytest.mark.parametrize("role", ["executive", "auditor", "alert-source"])
def test_other_roles_may_not_start_triage(role: str) -> None:
    with pytest.raises(PolicyDeniedError, match="workflow:run:triage"):
        DEFAULT_REGISTRY.authorize_start(_principal(role), "triage")
