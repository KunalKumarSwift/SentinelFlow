"""Alerts raised by detection sources, and the entities they mention.

``Alert.raw`` holds attacker-influenced text (user agents, command lines). It is
stored read-only and must always be treated as untrusted data, never as instructions.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime
from types import MappingProxyType

from sentinelflow.domain._validation import require_aware, require_text


@dataclass(frozen=True, slots=True)
class Entities:
    """Things an alert or incident refers to; every field is optional."""

    user: str | None = None
    ip: str | None = None
    host: str | None = None
    access_key_id: str | None = None
    url: str | None = None
    email_id: str | None = None

    def present(self) -> dict[str, str]:
        """Return only the entity fields that have a value, keyed by field name."""
        values = ((f.name, getattr(self, f.name)) for f in fields(self))
        return {name: value for name, value in values if value is not None}


@dataclass(frozen=True, slots=True)
class Alert:
    """A single detection raised by a source such as a SIEM or the simulator."""

    id: str
    tenant_id: str
    source: str
    rule_id: str
    title: str
    observed_at: datetime
    entities: Entities
    raw: Mapping[str, str] = field(default_factory=dict[str, str], hash=False)

    def __post_init__(self) -> None:
        """Validate invariants and freeze ``raw`` into a read-only copy."""
        for name in ("id", "tenant_id", "source", "rule_id"):
            require_text(getattr(self, name), name)
        require_aware(self.observed_at, "observed_at")
        # A copy, so later changes to the caller's dict cannot alter the alert.
        object.__setattr__(self, "raw", MappingProxyType(dict(self.raw)))
