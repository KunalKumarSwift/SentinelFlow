"""Builds LifecycleDeps for a simulator scenario with fakes (used by the Harness)."""

from dataclasses import dataclass

from sentinelflow.contracts.repositories import AlertRepository
from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.events.memory_event_store import MemoryEventStore
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from sentinelflow.providers.storage.memory_approvals import MemoryApprovalRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.providers.storage.memory_runs import MemoryRunRepository
from sentinelflow.providers.ticketing.memory_ticketing import MemoryTicketing
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.policy_engine import InCodePolicyEngine
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.tool_guard import ToolGuard
from sentinelflow.simulator.output import ScenarioOutput
from sentinelflow.workflows.investigation import InvestigationDeps, build_investigation_graph
from sentinelflow.workflows.orchestrator import LifecycleDeps
from sentinelflow.workflows.registry import DEFAULT_REGISTRY
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_identity import FakeIdentityProvider
from tests.fakes.fake_ids import SequentialIdFactory
from tests.fakes.fake_llm import FakeLLM
from tests.unit.workflows.investigation.helpers import answer
from tests.unit.workflows.triage.helpers import FP, TP


@dataclass(frozen=True)
class Stores:
    """The repositories a harness inspects."""

    incidents: MemoryIncidentRepository
    approvals: MemoryApprovalRepository
    runs: MemoryRunRepository
    audit: MemoryAuditStore
    ticketing: MemoryTicketing
    clock: FakeClock


def scripted_llm(scenario: str) -> FakeLLM:
    """Return an LLM scripted for triage, investigation and reporting.

    Only the brute-force family gets a scripted investigation answer; for the other
    scenarios the model is silent there, so the rule's playbook defaults apply.
    """
    scripted = scenario in {"brute_force", "prompt_injection"}
    return FakeLLM(
        {
            "triage.classify": FP if scenario == "benign_travel" else TP,
            "investigation.analyse": answer()
            if scripted
            else ProviderError("silent", retryable=False),
            "report.write": {"markdown": "# Report\nContained."},
        }
    )


def lifecycle_deps(
    stores: Stores, alerts: AlertRepository, out: ScenarioOutput, identity: FakeIdentityProvider
) -> LifecycleDeps:
    """Wire the lifecycle for ``out`` using ``stores``."""
    llm = scripted_llm(out.name)
    intel = MockThreatIntel(out.seed_data.ip_reputations)
    recorder = AuditRecorder(stores.audit, stores.clock)
    return LifecycleDeps(
        incidents=stores.incidents,
        alerts=alerts,
        approvals=stores.approvals,
        runs=stores.runs,
        triage=build_triage_graph(TriageDeps(intel, identity, llm)),
        investigation=build_investigation_graph(
            InvestigationDeps(MemoryEventStore(out.events), llm)
        ),
        guard=ToolGuard(InCodePolicyEngine(), recorder),
        identity=identity,
        recorder=recorder,
        clock=stores.clock,
        ids=SequentialIdFactory(),
        containment_scope=DEFAULT_REGISTRY.get("containment").max_scope,
        llm=llm,
        audit=stores.audit,
        ticketing=stores.ticketing,
        redactor=Redactor(b"r" * 32),
    )
