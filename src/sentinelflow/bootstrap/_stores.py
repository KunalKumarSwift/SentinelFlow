"""In-memory storage for single-process mode, bundled so wiring functions stay small."""

from dataclasses import dataclass, field
from datetime import timedelta

from sentinelflow.core.clock import Clock
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_approvals import MemoryApprovalRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.providers.storage.memory_runs import MemoryRunRepository
from sentinelflow.providers.ticketing.memory_ticketing import MemoryTicketing

VISIBILITY_TIMEOUT = timedelta(seconds=60)


@dataclass(frozen=True, slots=True)
class Stores:
    """Every repository and the run queue, shared by API and worker."""

    clock: Clock
    alerts: MemoryAlertRepository = field(default_factory=MemoryAlertRepository)
    incidents: MemoryIncidentRepository = field(default_factory=MemoryIncidentRepository)
    approvals: MemoryApprovalRepository = field(default_factory=MemoryApprovalRepository)
    runs: MemoryRunRepository = field(default_factory=MemoryRunRepository)
    audit: MemoryAuditStore = field(default_factory=MemoryAuditStore)
    ticketing: MemoryTicketing = field(default_factory=MemoryTicketing)
    queue: MemoryRunQueue = field(init=False)

    def __post_init__(self) -> None:
        """Create the queue with the shared clock."""
        object.__setattr__(self, "queue", MemoryRunQueue(self.clock, VISIBILITY_TIMEOUT))
