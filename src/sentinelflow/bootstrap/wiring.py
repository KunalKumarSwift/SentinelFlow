"""Build the single-process runtime: API container plus one worker sharing in-memory stores.

Phase 2 still supports in-memory storage and queue and mock intel/identity only; other
backends are rejected here so a misconfiguration fails at start-up, not mid-run.
"""

import hashlib
from dataclasses import dataclass

from sentinelflow.api.container import ApiContainer
from sentinelflow.bootstrap._lifecycle import build_lifecycle
from sentinelflow.bootstrap._stores import Stores
from sentinelflow.core.clock import SystemClock
from sentinelflow.core.config import Settings
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.facades.llm_facade import make_llm
from sentinelflow.runtime.dispatch import Dispatcher
from sentinelflow.runtime.resume_handler import ResumeRunHandler
from sentinelflow.runtime.start_handler import StartRunHandler
from sentinelflow.runtime.worker import Worker
from sentinelflow.security.policy_engine import InCodePolicyEngine
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.tokens import Hs256TokenService
from sentinelflow.workflows.ingestion import IngestionDeps, IngestionService
from sentinelflow.workflows.registry import DEFAULT_REGISTRY

DEFAULT_TEAM = "soc-emea"


@dataclass(frozen=True, slots=True)
class Runtime:
    """The wired application: HTTP container and the worker that drains its queue."""

    container: ApiContainer
    worker: Worker


def build_runtime(settings: Settings, demo_seed: int = 42) -> Runtime:
    """Wire every component for single-process mode.

    Raises:
        ValueError: If settings ask for a backend this phase does not provide.
    """
    _require_memory_backends(settings)
    stores = Stores(SystemClock())
    redactor = Redactor(_derive_key(settings.jwt_secret.get_secret_value(), "pii"))
    graph = build_lifecycle(stores, make_llm(settings), redactor, demo_seed)
    handler = Dispatcher(
        StartRunHandler(stores.runs, graph, stores.clock),
        ResumeRunHandler(stores.runs, graph, stores.clock),
    )
    worker = Worker(stores.queue, handler, "worker-1")
    return Runtime(_container(settings, stores, redactor), worker)


def _container(settings: Settings, stores: Stores, redactor: Redactor) -> ApiContainer:
    ids, secret = UuidIdFactory(), settings.jwt_secret.get_secret_value()
    deps = IngestionDeps(stores.alerts, stores.incidents, ids, stores.clock, DEFAULT_TEAM)
    return ApiContainer(
        app_env=settings.app_env,
        tokens=Hs256TokenService(secret, stores.clock),
        ingestion=IngestionService(deps),
        incidents=stores.incidents,
        registry=DEFAULT_REGISTRY,
        queue=stores.queue,
        runs=stores.runs,
        approvals=stores.approvals,
        policy=InCodePolicyEngine(),
        ids=ids,
        audit=stores.audit,
        clock=stores.clock,
        redactor=redactor,
        ticketing=stores.ticketing,
    )


def _derive_key(secret: str, purpose: str) -> bytes:
    # Domain separation: the token-signing secret is never used directly for pseudonyms.
    return hashlib.sha256(f"sentinelflow:{purpose}:{secret}".encode()).digest()


def _require_memory_backends(settings: Settings) -> None:
    chosen = (settings.storage_backend, settings.queue_backend, settings.intel_backend)
    if chosen != ("memory", "memory", "mock"):
        raise ValueError(
            f"single-process mode supports memory storage/queue and mock intel, got {chosen}"
        )
