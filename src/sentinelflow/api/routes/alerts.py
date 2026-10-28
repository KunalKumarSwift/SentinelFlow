"""``POST /v1/alerts``: ingest an alert and queue triage for new incidents."""

from typing import Annotated

from fastapi import APIRouter, Depends

from sentinelflow.api.auth import Auth
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.runs import enqueue_triage
from sentinelflow.api.schemas.alerts import AlertAccepted, AlertIn
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission


def build_alerts_router(container: ApiContainer, auth: Auth) -> APIRouter:
    """Return the alerts router."""
    router = APIRouter(prefix="/v1/alerts", tags=["alerts"])
    can_ingest = auth.require(Permission.ALERT_INGEST)

    @router.post("", status_code=202)
    def ingest_alert(
        body: AlertIn, principal: Annotated[Principal, Depends(can_ingest)]
    ) -> AlertAccepted:
        """Store the alert; a new incident gets a triage run queued."""
        result = container.ingestion.ingest(body.to_domain(principal, container.ids))
        details = {"incident_id": result.incident_id, "deduplicated": str(result.deduplicated)}
        container.recorder().record(principal, "alert.ingested", result.alert_id, details)
        run_id = None
        if not result.deduplicated:
            run_id = enqueue_triage(container, principal, result.incident)
        return AlertAccepted(
            alert_id=result.alert_id,
            incident_id=result.incident_id,
            deduplicated=result.deduplicated,
            run_id=run_id,
        )

    return router
