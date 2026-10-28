"""Audit response models."""

from datetime import datetime

from pydantic import BaseModel

from sentinelflow.domain.audit import AuditEvent


class AuditEventOut(BaseModel):
    """One audit record including its hash links."""

    seq: int
    at: datetime
    actor: str
    verb: str
    resource: str
    outcome: str
    details: dict[str, str]
    prev_hash: str
    hash: str

    @classmethod
    def of(cls, event: AuditEvent) -> "AuditEventOut":
        """Map a domain event."""
        return cls(
            seq=event.seq,
            at=event.at,
            actor=event.actor,
            verb=event.verb,
            resource=event.resource,
            outcome=event.outcome,
            details=dict(event.details),
            prev_hash=event.prev_hash,
            hash=event.hash,
        )


class AuditPage(BaseModel):
    """A page of audit records."""

    items: list[AuditEventOut]


class VerifyOut(BaseModel):
    """Chain verification result."""

    ok: bool
    first_bad_seq: int | None
    checked: int
