"""Write audit events on behalf of a principal, stamping tenant, actor, time and outcome.

The outcome follows the verb's suffix (``*.denied`` → denied, ``*.failed`` → failed,
otherwise ok) so call sites cannot record a denial as a success by mistake.
"""

from collections.abc import Mapping

from sentinelflow.contracts.audit_store import AuditStore
from sentinelflow.core.clock import Clock
from sentinelflow.domain.audit import AuditEvent, AuditEventDraft
from sentinelflow.domain.principals import Principal


class AuditRecorder:
    """Thin, injectable front for an ``AuditStore``."""

    def __init__(self, store: AuditStore, clock: Clock) -> None:
        """Record into ``store`` with timestamps from ``clock``."""
        self._store, self._clock = store, clock

    def record(
        self,
        actor: Principal,
        verb: str,
        resource: str,
        details: Mapping[str, str] | None = None,
    ) -> AuditEvent:
        """Append one event to the actor's tenant chain and return it."""
        draft = AuditEventDraft(
            tenant_id=actor.tenant_id,
            at=self._clock.now(),
            actor=actor.subject,
            verb=verb,
            resource=resource,
            outcome=_outcome(verb),
            details=details or {},
        )
        return self._store.append(draft)


def _outcome(verb: str) -> str:
    if verb.endswith(".denied"):
        return "denied"
    if verb.endswith(".failed"):
        return "failed"
    return "ok"
