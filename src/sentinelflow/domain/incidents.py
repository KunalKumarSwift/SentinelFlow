"""Incidents: one or more related alerts that are triaged and handled together."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sentinelflow.domain._validation import require_aware, require_text
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.errors import InvalidValueError
from sentinelflow.domain.severity import Severity


class IncidentStatus(StrEnum):
    """Lifecycle stage of an incident (see the state machine in LLD 01)."""

    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    AWAITING_APPROVAL = "awaiting_approval"
    CONTAINING = "containing"
    CONTAINED = "contained"
    ESCALATED = "escalated"
    CLOSED = "closed"


class Verdict(StrEnum):
    """Triage conclusion about whether the incident is a real attack."""

    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class Incident:
    """A group of related alerts owned by one team within one tenant."""

    id: str
    tenant_id: str
    team: str
    status: IncidentStatus
    severity: Severity
    verdict: Verdict | None
    alert_ids: tuple[str, ...]
    entities: Entities
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate identifiers, timestamps and that at least one alert exists."""
        for name in ("id", "tenant_id", "team"):
            require_text(getattr(self, name), name)
        require_aware(self.created_at, "created_at")
        if not self.alert_ids:
            raise InvalidValueError("alert_ids must contain at least one alert id")


def with_alert(incident: Incident, alert_id: str) -> Incident:
    """Return a copy of ``incident`` that also groups ``alert_id`` (idempotent)."""
    if alert_id in incident.alert_ids:
        return incident
    return replace(incident, alert_ids=(*incident.alert_ids, alert_id))
