"""API test wiring: an app built from in-memory parts and helpers to mint tokens."""

from collections.abc import Callable
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from sentinelflow.api.app import create_app
from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.providers.storage.memory_alerts import MemoryAlertRepository
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from sentinelflow.providers.storage.memory_incidents import MemoryIncidentRepository
from sentinelflow.providers.storage.memory_runs import MemoryRunRepository
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.tokens import Hs256TokenService
from sentinelflow.workflows.ingestion import IngestionDeps, IngestionService
from sentinelflow.workflows.registry import DEFAULT_REGISTRY
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_ids import SequentialIdFactory

SECRET = "a" * 32
TokenFor = Callable[..., dict[str, str]]


@pytest.fixture
def tokens() -> Hs256TokenService:
    return Hs256TokenService(secret=SECRET, clock=FakeClock(T0))


def make_container(tokens: Hs256TokenService, app_env: str = "dev") -> ApiContainer:
    """Return a container wired with in-memory parts and deterministic ids/time."""
    clock, ids = FakeClock(T0), SequentialIdFactory()
    incidents = MemoryIncidentRepository()
    ingestion = IngestionService(
        IngestionDeps(MemoryAlertRepository(), incidents, ids, clock, default_team="soc-emea")
    )
    return ApiContainer(
        app_env=app_env,
        tokens=tokens,
        ingestion=ingestion,
        incidents=incidents,
        registry=DEFAULT_REGISTRY,
        queue=MemoryRunQueue(clock, timedelta(seconds=60)),
        runs=MemoryRunRepository(),
        ids=ids,
        audit=MemoryAuditStore(),
        clock=clock,
        redactor=Redactor(b"r" * 32),
    )


@pytest.fixture
def container(tokens: Hs256TokenService) -> ApiContainer:
    return make_container(tokens)


@pytest.fixture
def client(container: ApiContainer) -> TestClient:
    return TestClient(create_app(container))


@pytest.fixture
def auth(tokens: Hs256TokenService) -> TokenFor:
    """Return Authorization headers for a principal with the given roles."""

    def headers(*roles: str, tenant: str = "acme", kind: str = "user") -> dict[str, str]:
        principal = Principal("u-1", tenant, "soc-emea", frozenset(roles), PrincipalKind(kind))
        return {"Authorization": f"Bearer {tokens.issue(principal)}"}

    return headers
