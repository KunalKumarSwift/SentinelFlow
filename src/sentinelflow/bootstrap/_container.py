"""Build the API container from the shared stores (kept apart so wiring stays small)."""

from sentinelflow.api.container import ApiContainer
from sentinelflow.bootstrap._stores import Stores
from sentinelflow.contracts.metrics import Metrics
from sentinelflow.core.config import Settings
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.facades.auth_facade import make_verifier
from sentinelflow.facades.policy_facade import make_policy_engine
from sentinelflow.facades.shared_state_facade import make_rate_limiter
from sentinelflow.security.redaction import Redactor
from sentinelflow.security.throttle import Throttle
from sentinelflow.security.tokens import Hs256TokenService
from sentinelflow.workflows.ingestion import IngestionDeps, IngestionService
from sentinelflow.workflows.registry import DEFAULT_REGISTRY

DEFAULT_TEAM = "soc-emea"


def build_container(
    settings: Settings, stores: Stores, redactor: Redactor, metrics: Metrics
) -> ApiContainer:
    """Return the HTTP layer's dependencies."""
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
        policy=make_policy_engine(settings),
        ids=ids,
        audit=stores.audit,
        clock=stores.clock,
        redactor=redactor,
        ticketing=stores.ticketing,
        throttle=Throttle(make_rate_limiter(settings, stores.clock)),
        metrics=metrics,
        verifier=make_verifier(settings, stores.clock),
    )
