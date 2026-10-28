"""Audit-store decorator that counts events by verb (policy denials included)."""

from collections.abc import Sequence

from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.contracts.metrics import Metrics
from sentinelflow.domain.audit import AuditEvent, AuditEventDraft


class CountingAuditStore:
    """Delegates to ``inner`` and reports every append to ``metrics``."""

    def __init__(self, inner: AuditStore, metrics: Metrics) -> None:
        """Wrap ``inner``."""
        self._inner, self._metrics = inner, metrics

    def append(self, draft: AuditEventDraft) -> AuditEvent:
        """Append, then count the verb."""
        event = self._inner.append(draft)
        self._metrics.audit_event(draft.verb)
        return event

    def read(self, tenant_id: str, after_seq: int, limit: int) -> Sequence[AuditEvent]:
        """Read straight from ``inner``."""
        return self._inner.read(tenant_id, after_seq, limit)
