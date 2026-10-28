"""Liveness endpoint (public)."""

from fastapi import APIRouter


def build_health_router() -> APIRouter:
    """Return the router serving ``GET /healthz``."""
    router = APIRouter(tags=["health"])

    @router.get("/healthz")
    def healthz() -> dict[str, str]:
        """Report that the process is up."""
        return {"status": "ok"}

    return router
