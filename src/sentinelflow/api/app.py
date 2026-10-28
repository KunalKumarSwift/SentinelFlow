"""Application factory: one FastAPI app per container, no global state."""

from fastapi import FastAPI

from sentinelflow import __version__
from sentinelflow.api import correlation, problems
from sentinelflow.api.auth import Auth
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.routes.alerts import build_alerts_router
from sentinelflow.api.routes.approvals import build_approvals_router
from sentinelflow.api.routes.audit import build_audit_router
from sentinelflow.api.routes.dev_auth import build_dev_auth_router
from sentinelflow.api.routes.health import build_health_router
from sentinelflow.api.routes.incidents import build_incidents_router
from sentinelflow.api.routes.runs import build_runs_router
from sentinelflow.api.routes.workflows import build_workflows_router


def create_app(container: ApiContainer) -> FastAPI:
    """Build the API around ``container``.

    Note:
        The dev-token router is mounted only when ``app_env == "dev"``; elsewhere the
        path does not exist at all (404), rather than existing and refusing.
    """
    app = FastAPI(title="SentinelFlow", version=__version__)
    problems.install(app)
    correlation.install(app, container.ids, container.clock)
    auth = Auth(container.tokens, container.recorder(), container.throttle)
    app.include_router(build_health_router())
    app.include_router(build_alerts_router(container, auth))
    app.include_router(build_incidents_router(container, auth))
    app.include_router(build_workflows_router(container, auth))
    app.include_router(build_audit_router(container, auth))
    app.include_router(build_approvals_router(container, auth))
    app.include_router(build_runs_router(container, auth))
    if container.app_env == "dev":
        app.include_router(build_dev_auth_router(container.tokens))
    return app
