"""Catalogue of runnable workflows and who may start them.

Each definition declares the permission needed to start it and its ``max_scope``:
the most it may ever do. The tool guard (Phase 2) intersects that scope with the
initiator's permissions, so a workflow can never act beyond what both allow.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from sentinelflow.domain.errors import PolicyDeniedError, UnknownWorkflowError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission
from sentinelflow.security.rbac import has_permission


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """A registered, versioned workflow and the permissions that govern it."""

    name: str
    version: str
    required_permission: Permission
    max_scope: frozenset[Permission]


class WorkflowRegistry:
    """Immutable lookup of workflow definitions by name."""

    def __init__(self, definitions: Iterable[WorkflowDefinition]) -> None:
        """Index ``definitions`` by name."""
        self._by_name = {d.name: d for d in definitions}

    def list(self) -> Sequence[WorkflowDefinition]:
        """Return all definitions sorted by name."""
        return sorted(self._by_name.values(), key=lambda d: d.name)

    def get(self, name: str) -> WorkflowDefinition:
        """Return the definition for ``name``.

        Raises:
            UnknownWorkflowError: If nothing is registered under ``name``.
        """
        definition = self._by_name.get(name)
        if definition is None:
            raise UnknownWorkflowError(f"no workflow named {name!r}")
        return definition

    def authorize_start(self, principal: Principal, name: str) -> WorkflowDefinition:
        """Return the definition if ``principal`` may start it.

        Raises:
            UnknownWorkflowError: If nothing is registered under ``name``.
            PolicyDeniedError: If the principal lacks the required permission.
        """
        definition = self.get(name)
        if not has_permission(principal, definition.required_permission):
            raise PolicyDeniedError(f"missing permission {definition.required_permission}")
        return definition


DEFAULT_REGISTRY = WorkflowRegistry(
    [
        WorkflowDefinition(
            name="containment",
            version="1.0.0",
            required_permission=Permission.RUN_CONTAINMENT,
            max_scope=frozenset({Permission.ACTION_PROPOSE, Permission.ACTION_EXECUTE}),
        ),
        WorkflowDefinition(
            name="triage",
            version="1.0.0",
            required_permission=Permission.RUN_TRIAGE,
            max_scope=frozenset({Permission.INTEL_LOOKUP, Permission.IDENTITY_READ}),
        ),
    ]
)
