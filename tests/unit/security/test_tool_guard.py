"""Tests for the tool guard: scope ∩ initiator ∩ orchestrator, every call audited."""

import pytest

from sentinelflow.domain.errors import PolicyDeniedError, ProviderError
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.permissions import Permission as Perm
from sentinelflow.security.policy import ActionContext
from sentinelflow.security.policy_engine import InCodePolicyEngine
from sentinelflow.security.tool_guard import RunContext, ToolCall, ToolGuard
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.unit.security.policy_helpers import incident, who

SCOPE = frozenset({Perm.ACTION_PROPOSE, Perm.ACTION_EXECUTE})
PROPOSE = ToolCall("call-1", Perm.ACTION_PROPOSE, incident())


def _guard() -> tuple[ToolGuard, MemoryAuditStore]:
    store = MemoryAuditStore()
    return ToolGuard(InCodePolicyEngine(), AuditRecorder(store, FakeClock(T0))), store


def _ctx(*roles: str, scope: frozenset[Perm] = SCOPE) -> RunContext:
    return RunContext("run-1", who(*roles), scope)


def _verbs(store: MemoryAuditStore) -> list[str]:
    return [e.verb for e in store.read("acme", 0, 50)]


def test_allowed_call_runs_effect_with_idempotency_key_and_is_audited() -> None:
    guard, store = _guard()
    assert guard.run(PROPOSE, _ctx("soc-analyst-l1"), lambda key: key) == "run-1:call-1"
    assert _verbs(store) == ["tool.allowed"]


def test_permission_outside_workflow_scope_is_denied() -> None:
    guard, store = _guard()
    with pytest.raises(PolicyDeniedError, match="outside workflow scope"):
        guard.run(PROPOSE, _ctx("soc-analyst-l1", scope=frozenset()), lambda key: key)
    assert _verbs(store) == ["tool.denied"]


def test_initiator_without_permission_is_denied() -> None:
    guard, _ = _guard()
    with pytest.raises(PolicyDeniedError, match="initiator: missing permission action:propose"):
        guard.run(PROPOSE, _ctx("executive"), lambda key: key)


def test_execute_without_quorum_is_denied_for_orchestrator() -> None:
    guard, _ = _guard()
    call = ToolCall("call-2", Perm.ACTION_EXECUTE, incident(), ActionContext(quorum_met=False))
    with pytest.raises(PolicyDeniedError, match="orchestrator: approval quorum not met"):
        guard.run(call, _ctx("soc-analyst-l1"), lambda key: key)


def test_execute_with_quorum_skips_initiator_check() -> None:
    guard, _ = _guard()
    call = ToolCall("call-2", Perm.ACTION_EXECUTE, incident(), ActionContext(quorum_met=True))
    assert guard.run(call, _ctx("soc-analyst-l1"), lambda key: "done") == "done"


def test_cross_tenant_call_is_denied() -> None:
    guard, _ = _guard()
    call = ToolCall("call-3", Perm.ACTION_PROPOSE, incident(tenant="globex"))
    with pytest.raises(PolicyDeniedError, match="another tenant"):
        guard.run(call, _ctx("soc-analyst-l1"), lambda key: key)


def test_failing_effect_is_audited_and_reraised() -> None:
    guard, store = _guard()

    def boom(_: str) -> str:
        raise ProviderError("idp down", retryable=True)

    with pytest.raises(ProviderError):
        guard.run(PROPOSE, _ctx("soc-analyst-l1"), boom)
    assert _verbs(store) == ["tool.allowed", "tool.failed"]
