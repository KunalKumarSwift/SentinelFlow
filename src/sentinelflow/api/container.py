"""Everything the API needs, built once by the composition root (or by tests)."""

from dataclasses import dataclass

from sentinelflow.contracts.approvals import ApprovalRepository
from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.contracts.repositories import IncidentRepository
from sentinelflow.contracts.run_queue import RunQueue
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.contracts.ticketing import TicketingProvider
from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.policy import PolicyEngine
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.tokens import Hs256TokenService
from sentinelflow.workflows.ingestion import IngestionService
from sentinelflow.workflows.registry import WorkflowRegistry


@dataclass(frozen=True, slots=True)
class ApiContainer:
    """Injected services for the HTTP layer.

    Attributes:
        app_env: ``"dev"`` enables the dev-token endpoint; any other value hides it.
    """

    app_env: str
    tokens: Hs256TokenService
    ingestion: IngestionService
    incidents: IncidentRepository
    registry: WorkflowRegistry
    queue: RunQueue
    runs: RunRepository
    approvals: ApprovalRepository
    policy: PolicyEngine
    ids: IdFactory
    audit: AuditStore
    clock: Clock
    redactor: Redactor
    ticketing: TicketingProvider

    def recorder(self) -> AuditRecorder:
        """Return an audit recorder bound to this container's store and clock."""
        return AuditRecorder(self.audit, self.clock)
