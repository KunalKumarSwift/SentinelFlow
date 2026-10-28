"""What the UI reads from the API: validated, read-only views of the JSON responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _View(BaseModel):
    # Ignore fields the UI does not show, so additive API changes never break it.
    model_config = ConfigDict(frozen=True, extra="ignore")


class IncidentView(_View):
    """One row of ``GET /v1/incidents``."""

    id: str
    status: str
    severity: str
    verdict: str | None
    team: str
    entities: dict[str, str]
    alert_count: int


class ApprovalView(_View):
    """One row of ``GET /v1/approvals``."""

    id: str
    incident_id: str
    run_id: str
    action: str
    target: str
    impact: str
    required_role: str
    required_count: int
    decisions: int
    status: str
    expires_at: datetime


class AuditView(_View):
    """One event of ``GET /v1/audit``."""

    seq: int
    at: datetime
    actor: str
    verb: str
    resource: str
    outcome: str


class VerifyView(_View):
    """Result of ``GET /v1/audit/verify``."""

    ok: bool
    first_bad_seq: int | None
    checked: int
