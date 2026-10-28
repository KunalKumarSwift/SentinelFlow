"""Pure view helpers: what the UI tables show."""

from datetime import UTC, datetime

from sentinelflow.ui.models import ApprovalView, IncidentView
from sentinelflow.ui.views import approval_rows, incident_rows

AT = datetime(2026, 1, 1, tzinfo=UTC)


def _incident(id_: str, severity: str) -> IncidentView:
    return IncidentView(
        id=id_,
        status="new",
        severity=severity,
        verdict=None,
        team="soc",
        entities={"user": "bob", "ip": "203.0.113.9"},
        alert_count=2,
    )


def test_incidents_are_sorted_most_severe_first_with_readable_entities() -> None:
    rows = incident_rows(
        [_incident("a", "low"), _incident("b", "critical"), _incident("c", "high")]
    )
    assert [r["id"] for r in rows] == ["b", "c", "a"]
    assert rows[0]["entities"] == "ip=203.0.113.9, user=bob"
    assert rows[0]["verdict"] == "—"


def test_approval_rows_show_progress_towards_quorum() -> None:
    approval = ApprovalView(
        id="apr-1",
        incident_id="inc-1",
        run_id="run-1",
        action="revoke_access_key",
        target="AKIA...",
        impact="high",
        required_role="incident-commander",
        required_count=2,
        decisions=1,
        status="pending",
        expires_at=AT,
    )
    [row] = approval_rows([approval])
    assert row["approvals"] == "1 / 2" and row["role"] == "incident-commander"
