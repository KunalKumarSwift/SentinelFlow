"""Tamper-evident audit chain: each event hashes its content plus the previous hash.

    hash_n = SHA256(hash_{n-1} || canonical_json(seq, tenant, at, actor, verb, ...))
    hash_0 = SHA256("sentinelflow-genesis:" + tenant_id)

Editing, reordering or deleting any event breaks every later link, and
``verify_chain`` reports the first event whose link does not hold.
"""

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC

from sentinelflow.domain.audit import AuditEvent, AuditEventDraft


@dataclass(frozen=True, slots=True)
class VerifyResult:
    """Outcome of verifying one tenant's chain."""

    ok: bool
    first_bad_seq: int | None = None


def genesis_hash(tenant_id: str) -> str:
    """Return the anchor hash a tenant's chain starts from."""
    return _sha256(f"sentinelflow-genesis:{tenant_id}")


def chain_next(previous: AuditEvent | None, draft: AuditEventDraft) -> AuditEvent:
    """Sequence and hash ``draft`` after ``previous`` (``None`` for the first event)."""
    seq = 1 if previous is None else previous.seq + 1
    prev_hash = genesis_hash(draft.tenant_id) if previous is None else previous.hash
    return AuditEvent(
        seq=seq,
        tenant_id=draft.tenant_id,
        at=draft.at,
        actor=draft.actor,
        verb=draft.verb,
        resource=draft.resource,
        outcome=draft.outcome,
        details=draft.details,
        prev_hash=prev_hash,
        hash=_link(prev_hash, seq, draft),
    )


def verify_chain(tenant_id: str, events: Sequence[AuditEvent]) -> VerifyResult:
    """Check that ``events`` form an unbroken chain for ``tenant_id`` starting at seq 1."""
    expected_prev, expected_seq = genesis_hash(tenant_id), 1
    for event in events:
        intact = (
            event.tenant_id == tenant_id
            and event.seq == expected_seq
            and event.prev_hash == expected_prev
            and event.hash == _link(event.prev_hash, event.seq, event)
        )
        if not intact:
            return VerifyResult(ok=False, first_bad_seq=event.seq)
        expected_prev, expected_seq = event.hash, expected_seq + 1
    return VerifyResult(ok=True)


def _link(prev_hash: str, seq: int, event: AuditEventDraft | AuditEvent) -> str:
    content = [
        seq,
        event.tenant_id,
        event.at.astimezone(UTC).isoformat(),
        event.actor,
        event.verb,
        event.resource,
        event.outcome,
        sorted(event.details.items()),
    ]
    canonical = json.dumps(content, separators=(",", ":"), ensure_ascii=False)
    return _sha256(prev_hash + canonical)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
