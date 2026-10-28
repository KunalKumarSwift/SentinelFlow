"""``GET /v1/runs/{run_id}``: status of a workflow run."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from sentinelflow.api.auth import Auth
from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission


class RunOut(BaseModel):
    """A run's status and who it runs on behalf of."""

    id: str
    workflow: str
    incident_id: str
    status: str
    initiator: str
    updated_at: datetime


def build_runs_router(container: ApiContainer, auth: Auth) -> APIRouter:
    """Return the runs router."""
    router = APIRouter(prefix="/v1/runs", tags=["runs"])
    can_read = auth.require(Permission.INCIDENT_READ)

    @router.get("/{run_id}")
    def get_run(run_id: str, principal: Annotated[Principal, Depends(can_read)]) -> RunOut:
        """Return the run, or 404 if absent or owned by another tenant."""
        run = container.runs.get(principal.tenant_id, run_id)
        if run is None:
            raise NotFoundError(f"run {run_id} not found")
        return RunOut(
            id=run.id,
            workflow=run.workflow,
            incident_id=run.incident_id,
            status=run.status.value,
            initiator=run.initiator.subject,
            updated_at=run.updated_at,
        )

    return router
