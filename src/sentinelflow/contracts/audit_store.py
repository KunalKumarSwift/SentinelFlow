"""Interface of the append-only audit store."""

from collections.abc import Sequence
from typing import Protocol

from sentinelflow.domain.audit import AuditEvent, AuditEventDraft


class AuditStore(Protocol):
    """Append-only, per-tenant hash-chained event log. There is no update or delete."""

    def append(self, draft: AuditEventDraft) -> AuditEvent:
        """Sequence, hash and persist ``draft``; return the stored event."""
        ...

    def read(self, tenant_id: str, after_seq: int, limit: int) -> Sequence[AuditEvent]:
        """Return up to ``limit`` of the tenant's events with ``seq > after_seq``, in order."""
        ...
