"""Turn API views into table rows (pure functions, so the UI logic is unit-tested)."""

from collections.abc import Iterable

from sentinelflow.ui.models import ApprovalView, IncidentView

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
Row = dict[str, str]


def incident_rows(incidents: Iterable[IncidentView]) -> list[Row]:
    """Return incident rows, most severe first."""
    ordered = sorted(incidents, key=lambda i: (_SEVERITY_ORDER.get(i.severity, 9), i.id))
    return [
        {
            "id": i.id,
            "severity": i.severity,
            "status": i.status,
            "verdict": i.verdict or "—",
            "team": i.team,
            "entities": ", ".join(f"{k}={v}" for k, v in sorted(i.entities.items())),
            "alerts": str(i.alert_count),
        }
        for i in ordered
    ]


def approval_rows(approvals: Iterable[ApprovalView]) -> list[Row]:
    """Return approval rows with progress towards the quorum."""
    return [
        {
            "id": a.id,
            "incident": a.incident_id,
            "action": a.action,
            "target": a.target,
            "impact": a.impact,
            "role": a.required_role,
            "approvals": f"{a.decisions} / {a.required_count}",
            "expires": a.expires_at.isoformat(timespec="minutes"),
        }
        for a in approvals
    ]
