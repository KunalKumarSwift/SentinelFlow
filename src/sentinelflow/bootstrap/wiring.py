"""Build the Phase 1 single-process runtime: API container plus one worker.

Phase 1 supports in-memory storage and queue and mock intel/identity only; other
backends are rejected here so a misconfiguration fails at start-up, not mid-run.
"""

from dataclasses import dataclass
from datetime import timedelta

from sentinelflow.api.container import ApiContainer
from sentinelflow.core.clock import SystemClock
from sentinelflow.core.config import Settings
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.facades.llm_facade import make_llm
from sentinelflow.providers.identity.mock_identity import MockIdentity
from sentinelflow.providers.intel.mock_intel import MockThreatIntel
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.runtime.start_handler import StartRunHandler
from sentinelflow.runtime.worker import Worker
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.tokens import Hs256TokenService
from sentinelflow.simulator.demo_seed import demo_seed_data
from sentinelflow.workflows.ingestion import IngestionDeps, IngestionService
from sentinelflow.workflows.orchestrator import build_lifecycle_graph
from sentinelflow.workflows.registry import DEFAULT_REGISTRY
from sentinelflow.workflows.triage import TriageDeps, build_triage_graph

VISIBILITY_TIMEOUT = timedelta(seconds=60)
DEFAULT_TEAM = "soc-emea"


@dataclass(frozen=True, slots=True)
class Runtime:
    """The wired application: HTTP container and the worker that drains its queue."""

    container: ApiContainer
    worker: Worker


def build_runtime(settings: Settings, demo_seed: int = 42) -> Runtime:
    """Wire every component for single-process mode.

    Raises:
        ValueError: If settings ask for a backend that Phase 1 does not provide.
    """
    _require_phase_one_backends(settings)
    clock, ids = SystemClock(), UuidIdFactory()
    alerts, incidents = MemoryAlertRepository(), MemoryIncidentRepository()
    queue, audit = MemoryRunQueue(clock, VISIBILITY_TIMEOUT), MemoryAuditStore()
    seed = demo_seed_data(demo_seed)
    triage = TriageDeps(
        MockThreatIntel(seed.ip_reputations), MockIdentity(seed.users), make_llm(settings)
    )
    graph = build_lifecycle_graph(build_triage_graph(triage))
    handler = StartRunHandler(alerts, incidents, graph, AuditRecorder(audit, clock))
    ingestion = IngestionService(IngestionDeps(alerts, incidents, ids, clock, DEFAULT_TEAM))
    tokens = Hs256TokenService(settings.jwt_secret.get_secret_value(), clock)
    container = ApiContainer(
        settings.app_env, tokens, ingestion, incidents, DEFAULT_REGISTRY, queue, ids, audit, clock
    )
    return Runtime(container, Worker(queue, handler, "worker-1"))


def _require_phase_one_backends(settings: Settings) -> None:
    chosen = (settings.storage_backend, settings.queue_backend, settings.intel_backend)
    if chosen != ("memory", "memory", "mock"):
        raise ValueError(f"Phase 1 supports memory storage/queue and mock intel, got {chosen}")
