"""Dependencies of the lifecycle graph."""

from dataclasses import dataclass, field

from opentelemetry.trace import NoOpTracer, Tracer

from sentinelflow.contracts.approvals import ApprovalRepository
from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.contracts.identity import IdentityProvider
from sentinelflow.contracts.llm import LLMProvider
from sentinelflow.contracts.notifier import Notifier
from sentinelflow.contracts.repositories import AlertRepository, IncidentRepository
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.contracts.ticketing import TicketingProvider
from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.permissions import Permission
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.tool_guard import ToolGuard
from sentinelflow.workflows.investigation.graph import InvestigationGraph
from sentinelflow.workflows.triage.graph import TriageGraph


@dataclass(frozen=True, slots=True)
class LifecycleDeps:
    """Injected collaborators; built once in the composition root.

    Attributes:
        containment_scope: ``max_scope`` of the registered containment workflow.
        tracer: OpenTelemetry tracer for step spans; no-op unless tracing is configured.
        notifier: Where "approvals waiting" messages go; ``None`` sends nothing.
    """

    incidents: IncidentRepository
    alerts: AlertRepository
    approvals: ApprovalRepository
    runs: RunRepository
    triage: TriageGraph
    investigation: InvestigationGraph
    guard: ToolGuard
    identity: IdentityProvider
    recorder: AuditRecorder
    clock: Clock
    ids: IdFactory
    containment_scope: frozenset[Permission]
    llm: LLMProvider
    audit: AuditStore
    ticketing: TicketingProvider
    redactor: Redactor
    tracer: Tracer = field(default_factory=NoOpTracer)
    notifier: Notifier | None = None
