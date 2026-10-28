"""``GET /v1/workflows`` and ``POST /v1/workflows/{name}/runs``."""

from typing import Annotated

from fastapi import APIRouter, Depends

from sentinelflow.api.auth import Auth
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.runs import enqueue_triage
from sentinelflow.api.schemas.workflows import RunAccepted, StartRunIn, WorkflowOut
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission


def build_workflows_router(container: ApiContainer, auth: Auth) -> APIRouter:
    """Return the workflows router."""
    router = APIRouter(prefix="/v1/workflows", tags=["workflows"])
    can_read = auth.require(Permission.INCIDENT_READ)

    @router.get("")
    def list_workflows(_: Annotated[Principal, Depends(can_read)]) -> list[WorkflowOut]:
        """List registered workflows and the permission each needs."""
        return [
            WorkflowOut(name=d.name, version=d.version, required_permission=d.required_permission)
            for d in container.registry.list()
        ]

    @router.post("/{name}/runs", status_code=202)
    def start_run(
        name: str,
        body: StartRunIn,
        principal: Annotated[Principal, Depends(auth.current_principal)],
    ) -> RunAccepted:
        """Queue a run after checking the workflow's own start permission."""
        container.registry.authorize_start(principal, name)
        incident = container.incidents.get(principal.tenant_id, body.incident_id)
        if incident is None:
            raise NotFoundError(f"incident {body.incident_id} not found")
        return RunAccepted(run_id=enqueue_triage(container, principal, incident))

    return router
