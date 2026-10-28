"""Incident lifecycle as an explicit state machine.

Status changes happen only through named events, and every allowed move is listed in
one table. Anything not listed is illegal, so a bug or a forged request cannot, for
example, jump an incident from ``NEW`` straight to ``CONTAINING``.
"""

from collections.abc import Mapping
from dataclasses import replace
from enum import StrEnum
from types import MappingProxyType

from sentinelflow.domain.errors import InvalidTransitionError
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.incidents import IncidentStatus as S


class IncidentEvent(StrEnum):
    """Something that happened to an incident and may change its status."""

    TRIAGE_CONFIRMED = "triage_confirmed"
    TRIAGE_DISMISSED = "triage_dismissed"
    INVESTIGATION_STARTED = "investigation_started"
    ACTIONS_PROPOSED = "actions_proposed"
    NO_SAFE_ACTION = "no_safe_action"
    APPROVALS_GRANTED = "approvals_granted"
    APPROVAL_REJECTED = "approval_rejected"
    CONTAINMENT_DONE = "containment_done"
    REPORT_WRITTEN = "report_written"
    CLOSED_BY_ANALYST = "closed_by_analyst"


E = IncidentEvent

TRANSITIONS: Mapping[tuple[S, IncidentEvent], S] = MappingProxyType(
    {
        (S.NEW, E.TRIAGE_CONFIRMED): S.TRIAGED,
        (S.NEW, E.TRIAGE_DISMISSED): S.CLOSED,
        (S.TRIAGED, E.INVESTIGATION_STARTED): S.INVESTIGATING,
        (S.INVESTIGATING, E.ACTIONS_PROPOSED): S.AWAITING_APPROVAL,
        (S.INVESTIGATING, E.NO_SAFE_ACTION): S.ESCALATED,
        (S.AWAITING_APPROVAL, E.APPROVALS_GRANTED): S.CONTAINING,
        (S.AWAITING_APPROVAL, E.APPROVAL_REJECTED): S.ESCALATED,
        (S.CONTAINING, E.CONTAINMENT_DONE): S.CONTAINED,
        (S.CONTAINED, E.REPORT_WRITTEN): S.CLOSED,
        (S.ESCALATED, E.CLOSED_BY_ANALYST): S.CLOSED,
    }
)


def next_status(current: S, event: IncidentEvent) -> S:
    """Return the status an incident moves to when ``event`` happens.

    Args:
        current: The incident's current status.
        event: What happened.

    Returns:
        The new status.

    Raises:
        InvalidTransitionError: If ``event`` is not allowed in ``current``.
    """
    target = TRANSITIONS.get((current, event))
    if target is None:
        raise InvalidTransitionError(f"incident in status {current} cannot accept event {event}")
    return target


def transition(incident: Incident, event: IncidentEvent) -> Incident:
    """Return a copy of ``incident`` moved to the status that ``event`` leads to.

    Raises:
        InvalidTransitionError: If ``event`` is not allowed in the incident's status.
    """
    return replace(incident, status=next_status(incident.status, event))
