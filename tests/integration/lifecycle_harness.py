"""Wires the full lifecycle (triage → investigate → approvals → contain) with fakes."""

from dataclasses import dataclass, field

from langgraph.checkpoint.memory import InMemorySaver

from sentinelflow.contracts.repositories import StoredAlert
from sentinelflow.domain.approvals import Approval, ApprovalDecision, record_decision
from sentinelflow.domain.principals import Principal
from sentinelflow.domain.runs import RunRecord, RunStatus
from sentinelflow.providers.events.memory_event_store import MemoryEventStore
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_approvals import MemoryApprovalRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.providers.storage.memory_runs import MemoryRunRepository
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.policy_engine import InCodePolicyEngine
from sentinelflow.security.system_principals import orchestrator_for
from sentinelflow.security.tool_guard import ToolGuard
from sentinelflow.simulator.registry import SCENARIOS
from sentinelflow.workflows.investigation import InvestigationDeps, build_investigation_graph
from sentinelflow.workflows.orchestrator import (
    LifecycleDeps,
    build_lifecycle_graph,
    resume_lifecycle,
    run_lifecycle,
)
from sentinelflow.workflows.orchestrator.graph import LifecycleGraph
from sentinelflow.workflows.registry import DEFAULT_REGISTRY
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph
from tests.builders import T0, an_incident
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_identity import FakeIdentityProvider
from tests.fakes.fake_ids import SequentialIdFactory
from tests.fakes.fake_llm import FakeLLM
from tests.unit.simulator.conftest import make_context
from tests.unit.workflows.investigation.helpers import answer
from tests.unit.workflows.triage.helpers import FP, TP


@dataclass
class Harness:
    """In-memory lifecycle with handles for assertions."""

    incidents: MemoryIncidentRepository = field(default_factory=MemoryIncidentRepository)
    approvals: MemoryApprovalRepository = field(default_factory=MemoryApprovalRepository)
    runs: MemoryRunRepository = field(default_factory=MemoryRunRepository)
    audit: MemoryAuditStore = field(default_factory=MemoryAuditStore)
    clock: FakeClock = field(default_factory=lambda: FakeClock(T0))
    graph: LifecycleGraph | None = None
    identity: FakeIdentityProvider | None = None
    deps: LifecycleDeps | None = None

    def start(self, scenario: str, initiator: Principal | None = None) -> bool:
        """Build and run the lifecycle for the scenario's first alert; True if waiting."""
        run = self.build(scenario, initiator)
        return run_lifecycle(self.graph_for(scenario), run)

    def build(self, scenario: str, initiator: Principal | None = None) -> RunRecord:
        """Wire everything and store a queued run record without running it."""
        out = SCENARIOS[scenario](make_context())
        alert, alerts = out.alerts[0], MemoryAlertRepository()
        alerts.add(StoredAlert(alert, "fp", "inc-0001"))
        self.incidents.add(an_incident(entities=alert.entities, alert_ids=(alert.id,)))
        self.identity = FakeIdentityProvider(out.seed_data.users)
        llm = FakeLLM(
            {
                "triage.classify": FP if scenario == "benign_travel" else TP,
                "investigation.analyse": answer(),
            }
        )
        triage = build_triage_graph(
            TriageDeps(MockThreatIntel(out.seed_data.ip_reputations), self.identity, llm)
        )
        investigation = build_investigation_graph(
            InvestigationDeps(MemoryEventStore(out.events), llm)
        )
        recorder = AuditRecorder(self.audit, self.clock)
        deps = LifecycleDeps(
            self.incidents,
            alerts,
            self.approvals,
            self.runs,
            triage,
            investigation,
            ToolGuard(InCodePolicyEngine(), recorder),
            self.identity,
            recorder,
            self.clock,
            SequentialIdFactory(),
            DEFAULT_REGISTRY.get("containment").max_scope,
        )
        self.deps, self.graph = deps, build_lifecycle_graph(deps, InMemorySaver())
        who = initiator or orchestrator_for("acme")
        run = RunRecord("run-1", "acme", "triage", "inc-0001", alert.id, who, RunStatus.QUEUED, T0)
        self.runs.add(run)
        return run

    def graph_for(self, scenario: str) -> LifecycleGraph:
        """Return the graph built by ``build``."""
        assert self.graph is not None, scenario
        return self.graph

    def decide(self, approval: Approval, approver: str, approved: bool = True) -> None:
        """Record one decision straight in the repository (the API does this in 2.9)."""
        decision = ApprovalDecision(approver, approved, "reviewed", T0)
        current = self.approvals.get("acme", approval.id)
        assert current is not None
        self.approvals.update(record_decision(current, decision))

    def resume(self) -> bool:
        """Resume the paused run; return True if still waiting."""
        assert self.graph is not None
        return resume_lifecycle(self.graph, "run-1")
