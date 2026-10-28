"""Policy-engine vocabulary: what is asked, about what, and the answer.

Phase 4 adds an OPA-backed engine implementing the same ``PolicyEngine`` protocol and
is checked by the same tests.
"""

from dataclasses import dataclass
from typing import Protocol

from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission


@dataclass(frozen=True, slots=True)
class Resource:
    """The object a request targets, reduced to what policy needs."""

    kind: str
    id: str
    tenant_id: str
    team: str | None = None


@dataclass(frozen=True, slots=True)
class ActionContext:
    """Facts about a containment action, for approval and execution rules.

    Attributes:
        target_user: User the action affects (``None`` if it targets an IP or host).
        prior_approvers: Subjects who already decided on this approval.
        quorum_met: Whether enough distinct approvals exist to execute.
    """

    target_user: str | None = None
    proposer: str | None = None
    initiator: str | None = None
    prior_approvers: frozenset[str] = frozenset()
    approval_open: bool = True
    quorum_met: bool = False


@dataclass(frozen=True, slots=True)
class AccessRequest:
    """May ``principal`` use ``permission`` on ``resource``?"""

    principal: Principal
    permission: Permission
    resource: Resource
    action: ActionContext | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    """The answer, always with a human-readable reason (shown to users and audited)."""

    allowed: bool
    reason: str


class PolicyEngine(Protocol):
    """Decides access requests."""

    def evaluate(self, request: AccessRequest) -> Decision:
        """Return allow/deny with a reason."""
        ...
