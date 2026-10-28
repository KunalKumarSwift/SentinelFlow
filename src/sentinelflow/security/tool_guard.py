"""The single choke point for side-effecting tool calls inside workflows.

A call runs only if all three hold (effective permission = scope ∩ initiator ∩ orchestrator):

1. the permission is inside the workflow's declared ``max_scope``;
2. the run's initiator may use it (skipped for ``action:execute``: no human executes);
3. the orchestrator service principal may use it (this is where the approval-quorum
   rule for execution applies).

This blocks the confused deputy: a workflow never does more than the person who started
it, and never more than its own declaration. Every allow, deny and failure is audited.
"""

from collections.abc import Callable
from dataclasses import dataclass

from sentinelflow.domain.errors import PolicyDeniedError, ProviderError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.permissions import Permission
from sentinelflow.security.policy import (
    AccessRequest,
    ActionContext,
    Decision,
    PolicyEngine,
    Resource,
)
from sentinelflow.security.system_principals import orchestrator_for


@dataclass(frozen=True, slots=True)
class ToolCall:
    """One side effect a workflow wants to perform."""

    id: str
    permission: Permission
    resource: Resource
    action: ActionContext | None = None


@dataclass(frozen=True, slots=True)
class RunContext:
    """Who started the run and what the workflow may ever do."""

    run_id: str
    initiator: Principal
    max_scope: frozenset[Permission]


class ToolGuard:
    """Authorises, executes and audits tool calls."""

    def __init__(self, policy: PolicyEngine, recorder: AuditRecorder) -> None:
        """Decide with ``policy``; record with ``recorder``."""
        self._policy, self._recorder = policy, recorder

    def run[T](self, call: ToolCall, ctx: RunContext, effect: Callable[[str], T]) -> T:
        """Authorise ``call`` and run ``effect(idempotency_key)``.

        Raises:
            PolicyDeniedError: If any of the three checks denies the call.
            ProviderError: Re-raised from ``effect`` after recording ``tool.failed``.
        """
        decision = self.authorize(call, ctx)
        details = {"call": call.id, "permission": call.permission, "reason": decision.reason}
        if not decision.allowed:
            self._recorder.record(ctx.initiator, "tool.denied", call.resource.id, details)
            raise PolicyDeniedError(decision.reason)
        self._recorder.record(ctx.initiator, "tool.allowed", call.resource.id, details)
        try:
            return effect(f"{ctx.run_id}:{call.id}")
        except ProviderError as exc:
            failed = {**details, "error": str(exc)}
            self._recorder.record(ctx.initiator, "tool.failed", call.resource.id, failed)
            raise

    def authorize(self, call: ToolCall, ctx: RunContext) -> Decision:
        """Return the combined decision without running anything."""
        if call.permission not in ctx.max_scope:
            return Decision(False, f"{call.permission} is outside workflow scope")
        if call.permission is not Permission.ACTION_EXECUTE:
            denied = self._check("initiator", ctx.initiator, call)
            if denied is not None:
                return denied
        orchestrator = orchestrator_for(ctx.initiator.tenant_id)
        return self._check("orchestrator", orchestrator, call) or Decision(True, "allowed")

    def _check(self, label: str, principal: Principal, call: ToolCall) -> Decision | None:
        request = AccessRequest(principal, call.permission, call.resource, call.action)
        decision = self._policy.evaluate(request)
        return None if decision.allowed else Decision(False, f"{label}: {decision.reason}")
