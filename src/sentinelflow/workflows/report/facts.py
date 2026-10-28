"""Gather report facts from the incident, its approvals and its own audit events."""

from collections.abc import Iterable, Mapping

from sentinelflow.domain.actions import targets_user
from sentinelflow.domain.approvals import Approval
from sentinelflow.domain.audit import AuditEvent
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.report import ActionLine, ReportFacts
from sentinelflow.security.redaction import Redactor


def collect_facts(
    incident: Incident,
    approvals: Iterable[Approval],
    events: Iterable[AuditEvent],
    redactor: Redactor,
) -> ReportFacts:
    """Return the facts for ``incident``; user targets are pseudonymised."""
    latest = _latest_details(e for e in events if e.resource == incident.id)
    return ReportFacts(
        incident_id=incident.id,
        status=incident.status.value,
        severity=str(incident.severity),
        verdict="" if incident.verdict is None else incident.verdict.value,
        injection=_split(latest.get("incident.triaged", {}).get("injection", "")),
        techniques=_split(latest.get("incident.investigated", {}).get("techniques", "")),
        actions=tuple(_line(a, redactor) for a in approvals),
        executed=_split(latest.get("incident.contained", {}).get("executed", "")),
    )


def _latest_details(events: Iterable[AuditEvent]) -> dict[str, Mapping[str, str]]:
    return {event.verb: event.details for event in events}


def _split(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.split(",") if part)


def _line(approval: Approval, redactor: Redactor) -> ActionLine:
    action = approval.action
    target = (
        redactor.pseudonym("user", action.target) if targets_user(action.kind) else action.target
    )
    return ActionLine(action.kind.value, target, approval.status.value)
