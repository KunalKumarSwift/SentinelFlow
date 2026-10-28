"""``GET /v1/audit`` and ``GET /v1/audit/verify`` (auditors and platform admins)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from sentinelflow.api.auth import Auth
from sentinelflow.api.container import ApiContainer
from sentinelflow.api.schemas.audit import AuditEventOut, AuditPage, VerifyOut
from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.domain.audit import AuditEvent
from sentinelflow.domain.principals import Principal
from sentinelflow.security.audit_chain import verify_chain
from sentinelflow.security.permissions import Permission

PAGE = 500


def build_audit_router(container: ApiContainer, auth: Auth) -> APIRouter:
    """Return the audit router."""
    router = APIRouter(prefix="/v1/audit", tags=["audit"])
    can_read = auth.require(Permission.AUDIT_READ)
    can_verify = auth.require(Permission.AUDIT_VERIFY)

    @router.get("")
    def read_audit(
        principal: Annotated[Principal, Depends(can_read)],
        after_seq: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=PAGE)] = 100,
    ) -> AuditPage:
        """Return the caller's tenant's audit events after ``after_seq``."""
        events = container.audit.read(principal.tenant_id, after_seq, limit)
        return AuditPage(items=[AuditEventOut.of(e) for e in events])

    @router.get("/verify")
    def verify(principal: Annotated[Principal, Depends(can_verify)]) -> VerifyOut:
        """Re-hash the tenant's whole chain and report the first broken link."""
        events = read_all(container.audit, principal.tenant_id)
        result = verify_chain(principal.tenant_id, events)
        return VerifyOut(ok=result.ok, first_bad_seq=result.first_bad_seq, checked=len(events))

    return router


def read_all(store: AuditStore, tenant_id: str) -> list[AuditEvent]:
    """Read a tenant's entire chain page by page."""
    events: list[AuditEvent] = []
    while page := store.read(tenant_id, events[-1].seq if events else 0, PAGE):
        events.extend(page)
    return events
