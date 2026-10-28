"""Raw security events (log lines) that investigations search through.

``attributes`` carries source-specific, attacker-influenced text and is stored as a
read-only copy; like ``Alert.raw`` it is untrusted data.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType

from sentinelflow.domain._validation import require_aware, require_text
from sentinelflow.domain.alerts import Entities


@dataclass(frozen=True, slots=True)
class SecurityEvent:
    """One observed activity, e.g. a failed login or an API call."""

    id: str
    tenant_id: str
    at: datetime
    kind: str
    entities: Entities
    attributes: Mapping[str, str] = field(default_factory=dict[str, str], hash=False)

    def __post_init__(self) -> None:
        """Validate invariants and freeze ``attributes`` into a read-only copy."""
        for name in ("id", "tenant_id", "kind"):
            require_text(getattr(self, name), name)
        require_aware(self.at, "at")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))
