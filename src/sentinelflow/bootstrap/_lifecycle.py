"""Build the lifecycle graph (triage, investigation, approvals, containment) for one process."""

from langgraph.checkpoint.memory import InMemorySaver

from sentinelflow.bootstrap._stores import Stores
from sentinelflow.contracts.llm import LLMProvider
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.providers.events.memory_event_store import MemoryEventStore
from sentinelflow.providers.identity.mock_identity import MockIdentity
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.policy_engine import InCodePolicyEngine
from sentinelflow.security.tool_guard import ToolGuard
from sentinelflow.simulator.demo_seed import demo_events, demo_seed_data
from sentinelflow.workflows.investigation import InvestigationDeps, build_investigation_graph
from sentinelflow.workflows.orchestrator import LifecycleDeps, build_lifecycle_graph
from sentinelflow.workflows.orchestrator.graph import LifecycleGraph
from sentinelflow.workflows.registry import DEFAULT_REGISTRY
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph


def build_lifecycle(stores: Stores, llm: LLMProvider, demo_seed: int) -> LifecycleGraph:
    """Return the lifecycle graph wired to mock providers seeded for the demo."""
    seed = demo_seed_data(demo_seed)
    identity = MockIdentity(seed.users)
    triage = build_triage_graph(TriageDeps(MockThreatIntel(seed.ip_reputations), identity, llm))
    investigation = build_investigation_graph(
        InvestigationDeps(MemoryEventStore(demo_events(demo_seed)), llm)
    )
    recorder = AuditRecorder(stores.audit, stores.clock)
    deps = LifecycleDeps(
        incidents=stores.incidents,
        alerts=stores.alerts,
        approvals=stores.approvals,
        runs=stores.runs,
        triage=triage,
        investigation=investigation,
        guard=ToolGuard(InCodePolicyEngine(), recorder),
        identity=identity,
        recorder=recorder,
        clock=stores.clock,
        ids=UuidIdFactory(),
        containment_scope=DEFAULT_REGISTRY.get("containment").max_scope,
    )
    return build_lifecycle_graph(deps, InMemorySaver())
