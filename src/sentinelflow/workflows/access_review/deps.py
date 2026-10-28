"""Dependencies of the access-review graph."""

from dataclasses import dataclass

from sentinelflow.contracts.accounts import AccountDirectory
from sentinelflow.contracts.repositories import AlertRepository, IncidentRepository
from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory
from sentinelflow.workflows.ingestion import IngestionService


@dataclass(frozen=True, slots=True)
class AccessReviewDeps:
    """Injected collaborators; ``alerts``/``incidents`` detect findings still open."""

    directory: AccountDirectory
    ingestion: IngestionService
    alerts: AlertRepository
    incidents: IncidentRepository
    ids: IdFactory
    clock: Clock
