"""Build the runtime: API container plus one worker sharing the stores and metrics.

Storage may be memory or PostgreSQL and the queue memory or Redis; intel and identity
are mocks. Other backends are rejected here so a misconfiguration fails at start-up,
not mid-run.
"""

import hashlib
from dataclasses import dataclass, replace

from prometheus_client import CollectorRegistry

from sentinelflow.api.container import ApiContainer
from sentinelflow.bootstrap._container import build_container
from sentinelflow.bootstrap._lifecycle import Services, build_lifecycle
from sentinelflow.bootstrap._pg_stores import postgres_stores
from sentinelflow.bootstrap._stores import VISIBILITY_TIMEOUT, Stores, memory_stores
from sentinelflow.core.clock import SystemClock
from sentinelflow.core.config import Settings
from sentinelflow.facades.llm_facade import make_llm
from sentinelflow.facades.shared_state_facade import make_run_queue, make_token_budget
from sentinelflow.facades.tracing_facade import make_tracer
from sentinelflow.providers.llm.budgeted_llm import BudgetedLLM
from sentinelflow.providers.metrics.counting_audit_store import CountingAuditStore
from sentinelflow.providers.metrics.prometheus_metrics import PrometheusMetrics
from sentinelflow.runtime.dispatch import Dispatcher
from sentinelflow.runtime.resume_handler import ResumeRunHandler
from sentinelflow.runtime.start_handler import StartRunHandler
from sentinelflow.runtime.worker import Worker
from sentinelflow.security.redaction import Redactor


@dataclass(frozen=True, slots=True)
class Runtime:
    """The wired application: HTTP container, the worker and this process's metrics."""

    container: ApiContainer
    worker: Worker
    metrics: PrometheusMetrics


def build_runtime(settings: Settings, demo_seed: int = 42) -> Runtime:
    """Wire every component for one process.

    Raises:
        ValueError: If settings ask for a backend this phase does not provide.
    """
    _require_supported_backends(settings)
    metrics = PrometheusMetrics(CollectorRegistry())
    stores = _stores(settings, metrics)
    redactor = Redactor(_derive_key(settings.jwt_secret.get_secret_value(), "pii"))
    tracer = make_tracer(settings)
    services = Services(_budgeted_llm(settings, stores, metrics), redactor, tracer, demo_seed)
    graph = build_lifecycle(stores, services)
    handler = Dispatcher(
        StartRunHandler(stores.runs, graph, stores.clock),
        ResumeRunHandler(stores.runs, graph, stores.clock),
    )
    worker = Worker(stores.queue, handler, "worker-1", metrics=metrics, tracer=tracer)
    return Runtime(build_container(settings, stores, redactor, metrics), worker, metrics)


def _budgeted_llm(settings: Settings, stores: Stores, metrics: PrometheusMetrics) -> BudgetedLLM:
    budget = make_token_budget(settings, stores.clock)
    limit = settings.tenant_token_budget_daily
    return BudgetedLLM(make_llm(settings), budget, limit, metrics)


def _derive_key(secret: str, purpose: str) -> bytes:
    # Domain separation: the token-signing secret is never used directly for pseudonyms.
    return hashlib.sha256(f"sentinelflow:{purpose}:{secret}".encode()).digest()


def _stores(settings: Settings, metrics: PrometheusMetrics) -> Stores:
    clock = SystemClock()
    queue = make_run_queue(settings, clock, VISIBILITY_TIMEOUT)
    if settings.database_url is not None and settings.storage_backend == "postgres":
        stores = postgres_stores(clock, settings.database_url.get_secret_value(), queue)
    else:
        stores = memory_stores(clock, queue)
    # Every audit append (policy denials included) is counted, whoever writes it.
    return replace(stores, audit=CountingAuditStore(stores.audit, metrics))


def _require_supported_backends(settings: Settings) -> None:
    if settings.intel_backend != "mock":
        raise ValueError(f"intel backend {settings.intel_backend!r} is not available yet")
