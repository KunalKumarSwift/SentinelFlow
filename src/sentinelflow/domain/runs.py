"""Run records: one execution of a workflow for an incident, and who started it."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from sentinelflow.domain.principals import Principal


class RunStatus(StrEnum):
    """Lifecycle of a run as seen by API callers."""

    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RunRecord:
    """A workflow run; ``initiator`` is the principal whose authority the run carries."""

    id: str
    tenant_id: str
    workflow: str
    incident_id: str
    alert_id: str
    initiator: Principal
    status: RunStatus
    updated_at: datetime


def with_status(record: RunRecord, status: RunStatus, at: datetime) -> RunRecord:
    """Return ``record`` moved to ``status`` at time ``at``."""
    return replace(record, status=status, updated_at=at)
