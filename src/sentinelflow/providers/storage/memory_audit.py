"""In-memory audit store for tests and single-process mode."""

from collections import defaultdict
from collections.abc import Sequence
from threading import Lock

from sentinelflow.domain.audit import AuditEvent, AuditEventDraft
from sentinelflow.security.audit_chain import chain_next


class MemoryAuditStore:
    """Keeps one hash chain per tenant in a list."""

    def __init__(self) -> None:
        """Start empty."""
        self._chains: defaultdict[str, list[AuditEvent]] = defaultdict(list)
        # API threads and the worker thread append concurrently; seq must stay gap-free.
        self._lock = Lock()

    def append(self, draft: AuditEventDraft) -> AuditEvent:
        """Link ``draft`` to the end of its tenant's chain."""
        with self._lock:
            chain = self._chains[draft.tenant_id]
            event = chain_next(chain[-1] if chain else None, draft)
            chain.append(event)
            return event

    def read(self, tenant_id: str, after_seq: int, limit: int) -> Sequence[AuditEvent]:
        """Return a page of the tenant's events after ``after_seq``."""
        return [e for e in self._chains.get(tenant_id, []) if e.seq > after_seq][:limit]
