"""Tests for the incident lifecycle state machine."""

from itertools import product

import pytest

from sentinelflow.domain.errors import InvalidTransitionError
from sentinelflow.domain.incidents import IncidentStatus as S
from sentinelflow.domain.lifecycle import IncidentEvent as E
from sentinelflow.domain.lifecycle import next_status, transition
from tests.builders import an_incident

LEGAL = {
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
ILLEGAL = [pair for pair in product(S, E) if pair not in LEGAL]


@pytest.mark.parametrize(("current", "event"), list(LEGAL))
def test_legal_transition(current: S, event: E) -> None:
    assert next_status(current, event) is LEGAL[(current, event)]


@pytest.mark.parametrize(("current", "event"), ILLEGAL)
def test_every_other_transition_is_rejected(current: S, event: E) -> None:
    with pytest.raises(InvalidTransitionError, match=f"{current}.*{event}"):
        next_status(current, event)


def test_closed_is_terminal() -> None:
    assert all((S.CLOSED, event) in ILLEGAL for event in E)


def test_transition_returns_updated_copy() -> None:
    incident = an_incident(status=S.NEW)
    updated = transition(incident, E.TRIAGE_CONFIRMED)
    assert (incident.status, updated.status) == (S.NEW, S.TRIAGED)
    assert updated.id == incident.id
