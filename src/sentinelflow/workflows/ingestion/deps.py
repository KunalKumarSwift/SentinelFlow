"""Dependencies the ingestion service needs from the outside world."""

from dataclasses import dataclass

from sentinelflow.contracts.repositories import AlertRepository, IncidentRepository
from sentinelflow.core.clock import Clock
from sentinelflow.core.ids import IdFactory


@dataclass(frozen=True, slots=True)
class IngestionDeps:
    """Injected collaborators; built once in the composition root.

    Attributes:
        default_team: Team that owns new incidents until team routing exists.
    """

    alerts: AlertRepository
    incidents: IncidentRepository
    ids: IdFactory
    clock: Clock
    default_team: str
