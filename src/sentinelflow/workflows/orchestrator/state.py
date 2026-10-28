"""Checkpointed state of the lifecycle graph: identifiers only.

Domain objects live in repositories; steps load and save them. Checkpoints therefore
stay tiny, JSON-safe and never go stale (see ADR 0007).
"""

from typing import NotRequired, Protocol, TypedDict


class LifecycleState(TypedDict):
    """Which run, tenant, incident and alert this lifecycle is about."""

    run_id: str
    tenant_id: str
    incident_id: str
    alert_id: str
    approval_ids: NotRequired[list[str]]


class LifecycleUpdate(TypedDict, total=False):
    """Partial state a step returns."""

    approval_ids: list[str]


class Step(Protocol):
    """A lifecycle node."""

    def __call__(self, state: LifecycleState) -> LifecycleUpdate:
        """Run the step."""
        ...
