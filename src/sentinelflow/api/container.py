"""Everything the API needs, built once by the composition root (or by tests)."""

from dataclasses import dataclass

from sentinelflow.contracts.repositories import IncidentRepository
from sentinelflow.contracts.run_queue import RunQueue
from sentinelflow.core.ids import IdFactory
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
    ids: IdFactory
