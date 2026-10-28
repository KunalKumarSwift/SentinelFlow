"""``GET /v1/incidents`` and ``GET /v1/incidents/{id}`` (tenant-scoped)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from sentinelflow.api.auth import Auth
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.schemas.incidents import IncidentOut, IncidentPage
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission


def build_incidents_router(container: ApiContainer, auth: Auth) -> APIRouter:
    """Return the incidents router."""
    router = APIRouter(prefix="/v1/incidents", tags=["incidents"])
    can_read = auth.require(Permission.INCIDENT_READ)

    @router.get("")
    def list_incidents(principal: Annotated[Principal, Depends(can_read)]) -> IncidentPage:
        """List the caller's tenant's incidents, oldest first."""
        items = container.incidents.list(principal.tenant_id)
        return IncidentPage(items=[_view(i, principal) for i in items])

    @router.get("/{incident_id}")
    def get_incident(
        incident_id: str, principal: Annotated[Principal, Depends(can_read)]
    ) -> IncidentOut:
        """Return one incident; other tenants' incidents are reported as not found."""
        incident = container.incidents.get(principal.tenant_id, incident_id)
        if incident is None:
            raise NotFoundError(f"incident {incident_id} not found")
        return _view(incident, principal)

    def _view(incident: Incident, principal: Principal) -> IncidentOut:
        return IncidentOut.of(
            incident, container.redactor.entities_for(principal, incident.entities)
        )

    return router
