"""Audit records: what happened, who did it, and the hash links that make tampering visible."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class AuditEventDraft:
    """An event before it is sequenced and hashed into its tenant's chain.

    Attributes:
        verb: Dotted event name, e.g. ``"alert.ingested"`` or ``"policy.denied"``.
        outcome: ``"ok"``, ``"denied"``, ``"failed"`` or similar.
    """

    tenant_id: str
    at: datetime
    actor: str
    verb: str
    resource: str
    outcome: str
    details: Mapping[str, str] = field(default_factory=dict[str, str], hash=False)

    def __post_init__(self) -> None:
        """Freeze ``details`` into a read-only copy."""
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """A sequenced, hash-linked audit record (see ``security/audit_chain.py``)."""

    seq: int
    tenant_id: str
    at: datetime
    actor: str
    verb: str
    resource: str
    outcome: str
    details: Mapping[str, str] = field(hash=False)
    prev_hash: str
    hash: str
