"""Application factory: one FastAPI app per container, no global state."""

from fastapi import FastAPI

from sentinelflow import __version__
from sentinelflow.api import problems
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.routes.dev_auth import build_dev_auth_router
from sentinelflow.api.routes.health import build_health_router


def create_app(container: ApiContainer) -> FastAPI:
    """Build the API around ``container``.

    Note:
        The dev-token router is mounted only when ``app_env == "dev"``; elsewhere the
        path does not exist at all (404), rather than existing and refusing.
    """
    app = FastAPI(title="SentinelFlow", version=__version__)
    problems.install(app)
    app.include_router(build_health_router())
    if container.app_env == "dev":
        app.include_router(build_dev_auth_router(container.tokens))
    return app
