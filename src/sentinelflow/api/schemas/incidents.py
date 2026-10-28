"""Incident response models."""

from datetime import datetime

from pydantic import BaseModel

from sentinelflow.domain.incidents import Incident


class IncidentOut(BaseModel):
    """An incident as shown to API callers; ``entities`` is already redacted per role."""

    id: str
    status: str
    severity: str
    verdict: str | None
    team: str
    entities: dict[str, str]
    alert_count: int
    created_at: datetime

    @classmethod
    def of(cls, incident: Incident, entities: dict[str, str]) -> "IncidentOut":
        """Map a domain incident, using the caller-appropriate ``entities`` view."""
        return cls(
            id=incident.id,
            status=incident.status.value,
            severity=str(incident.severity),
            verdict=None if incident.verdict is None else incident.verdict.value,
            team=incident.team,
            entities=entities,
            alert_count=len(incident.alert_ids),
            created_at=incident.created_at,
        )


class IncidentPage(BaseModel):
    """A list of incidents."""

    items: list[IncidentOut]


class ReportOut(BaseModel):
    """A post-incident report."""

    ticket_id: str
    title: str
    body: str
