"""Build the lifecycle graph (triage, investigation, approvals, containment) for one process."""

from dataclasses import dataclass

from opentelemetry.trace import Tracer

from sentinelflow.bootstrap._stores import Stores
from sentinelflow.contracts.llm import LLMProvider
from sentinelflow.core.config import Settings
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.facades.intel_facade import make_threat_intel
from sentinelflow.facades.notify_facade import make_notifier
from sentinelflow.providers.events.memory_event_store import MemoryEventStore
from sentinelflow.providers.identity.mock_identity import MockIdentity
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.policy import PolicyEngine
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.tool_guard import ToolGuard
from sentinelflow.simulator.demo_seed import demo_events, demo_seed_data
from sentinelflow.workflows.investigation import InvestigationDeps, build_investigation_graph
from sentinelflow.workflows.orchestrator import LifecycleDeps, build_lifecycle_graph
from sentinelflow.workflows.orchestrator.graph import LifecycleGraph
from sentinelflow.workflows.registry import DEFAULT_REGISTRY
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph


@dataclass(frozen=True, slots=True)
class Services:
    """Process-wide collaborators of the lifecycle besides storage."""

    llm: LLMProvider
    redactor: Redactor
    tracer: Tracer
    demo_seed: int
    policy: PolicyEngine
    settings: Settings


def build_lifecycle(stores: Stores, services: Services) -> LifecycleGraph:
    """Return the lifecycle graph wired to mock providers seeded for the demo."""
    llm, redactor, demo_seed = services.llm, services.redactor, services.demo_seed
    seed = demo_seed_data(demo_seed)
    identity = MockIdentity(seed.users)
    intel = make_threat_intel(services.settings, seed.ip_reputations)
    triage = build_triage_graph(TriageDeps(intel, identity, llm))
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
        guard=ToolGuard(services.policy, recorder),
        identity=identity,
        recorder=recorder,
        clock=stores.clock,
        ids=UuidIdFactory(),
        containment_scope=DEFAULT_REGISTRY.get("containment").max_scope,
        llm=llm,
        audit=stores.audit,
        ticketing=stores.ticketing,
        redactor=redactor,
        tracer=services.tracer,
        notifier=make_notifier(services.settings),
    )
    return build_lifecycle_graph(deps, stores.checkpointer)
