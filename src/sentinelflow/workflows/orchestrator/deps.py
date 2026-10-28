"""Dependencies of the lifecycle graph."""

from dataclasses import dataclass

from sentinelflow.contracts.approvals import ApprovalRepository
from sentinelflow.contracts.identity import IdentityProvider
from sentinelflow.contracts.repositories import AlertRepository, IncidentRepository
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.permissions import Permission
from sentinelflow.security.tool_guard import ToolGuard
from sentinelflow.workflows.investigation.graph import InvestigationGraph
from sentinelflow.workflows.triage.graph import TriageGraph


@dataclass(frozen=True, slots=True)
class LifecycleDeps:
    """Injected collaborators; built once in the composition root.

    Attributes:
        containment_scope: ``max_scope`` of the registered containment workflow.
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
