"""Storage for one process, bundled so wiring functions stay small.

``memory_stores`` keeps everything in the process; ``postgres_stores`` persists the
repositories and LangGraph checkpoints so runs survive a restart. The run queue is
chosen separately (``QUEUE_BACKEND``) and passed in.
"""

from dataclasses import dataclass
from datetime import timedelta

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from sentinelflow.contracts.approvals import ApprovalRepository
from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.contracts.repositories import AlertRepository, IncidentRepository
from sentinelflow.contracts.run_queue import RunQueue
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.contracts.ticketing import TicketingProvider
from sentinelflow.core.clock import Clock
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_approvals import MemoryApprovalRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.providers.storage.memory_runs import MemoryRunRepository
from sentinelflow.providers.ticketing.memory_ticketing import MemoryTicketing

VISIBILITY_TIMEOUT = timedelta(seconds=60)


@dataclass(frozen=True, slots=True)
class Stores:
    """Every repository, the checkpointer and the run queue, shared by API and worker."""

    clock: Clock
    alerts: AlertRepository
    incidents: IncidentRepository
    approvals: ApprovalRepository
    runs: RunRepository
    audit: AuditStore
    checkpointer: BaseCheckpointSaver[str]
    ticketing: TicketingProvider
    queue: RunQueue


def memory_stores(clock: Clock, queue: RunQueue) -> Stores:
    """Return fresh in-memory stores around ``queue``."""
    return Stores(
        clock=clock,
        alerts=MemoryAlertRepository(),
        incidents=MemoryIncidentRepository(),
        approvals=MemoryApprovalRepository(),
        runs=MemoryRunRepository(),
        audit=MemoryAuditStore(),
        checkpointer=InMemorySaver(),
        ticketing=MemoryTicketing(),
        queue=queue,
    )
