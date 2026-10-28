"""Runs the full lifecycle (triage → investigate → approvals → contain → report) with fakes."""

from langgraph.checkpoint.memory import InMemorySaver

from sentinelflow.contracts.repositories import StoredAlert
from sentinelflow.domain.approvals import Approval, ApprovalDecision, record_decision
from sentinelflow.domain.principals import Principal
from sentinelflow.domain.runs import RunRecord, RunStatus
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_approvals import MemoryApprovalRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.providers.storage.memory_runs import MemoryRunRepository
from sentinelflow.providers.ticketing.memory_ticketing import MemoryTicketing
from sentinelflow.security.system_principals import orchestrator_for
from sentinelflow.simulator.registry import SCENARIOS
from sentinelflow.workflows.orchestrator import (
    LifecycleDeps,
    build_lifecycle_graph,
    resume_lifecycle,
    run_lifecycle,
)
from sentinelflow.workflows.orchestrator.graph import LifecycleGraph
from tests.builders import T0, an_incident
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_identity import FakeIdentityProvider
from tests.integration.lifecycle_wiring import Stores, lifecycle_deps
from tests.unit.simulator.conftest import make_context


class Harness:
    """In-memory lifecycle with handles for assertions."""

    def __init__(self) -> None:
        """Create empty stores and a fake clock."""
        self.stores = Stores(
            MemoryIncidentRepository(),
            MemoryApprovalRepository(),
            MemoryRunRepository(),
            MemoryAuditStore(),
            MemoryTicketing(),
            FakeClock(T0),
        )
        self.incidents, self.approvals, self.runs = (
            self.stores.incidents,
            self.stores.approvals,
            self.stores.runs,
        )
        self.audit, self.ticketing, self.clock = (
            self.stores.audit,
            self.stores.ticketing,
            self.stores.clock,
        )
        self.graph: LifecycleGraph | None = None
        self.identity: FakeIdentityProvider | None = None
        self.deps: LifecycleDeps | None = None
        self.saver = InMemorySaver()

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
        self.deps = lifecycle_deps(self.stores, alerts, out, self.identity)
        self.graph = build_lifecycle_graph(self.deps, self.saver)
        owner = initiator or orchestrator_for("acme")
        run = RunRecord(
            "run-1", "acme", "triage", "inc-0001", alert.id, owner, RunStatus.QUEUED, T0
        )
        self.runs.add(run)
        return run

    def graph_for(self, scenario: str) -> LifecycleGraph:
        """Return the graph built by ``build``."""
        assert self.graph is not None, scenario
        return self.graph

    def decide(self, approval: Approval, approver: str, approved: bool = True) -> None:
        """Record one decision straight in the repository (the API does this normally)."""
        current = self.approvals.get("acme", approval.id)
        assert current is not None
        decision = ApprovalDecision(approver, approved, "reviewed", T0)
        self.approvals.update(record_decision(current, decision))

    def resume(self) -> bool:
        """Resume the paused run; return True if still waiting."""
        return resume_lifecycle(self.graph_for("resume"), "run-1")
