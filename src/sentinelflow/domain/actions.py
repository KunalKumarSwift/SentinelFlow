"""Proposed containment actions and the approvals they require."""

from dataclasses import dataclass

from sentinelflow.domain._validation import require_text
from sentinelflow.domain.actions_table import APPROVER_ROLE, CATALOGUE, ActionKind, Impact
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.errors import UnknownActionError
from sentinelflow.domain.severity import Severity

__all__ = [
    "ActionKind",
    "ApprovalRequirement",
    "Impact",
    "ProposedAction",
    "approval_requirement",
    "parse_action_kind",
    "target_of",
]


@dataclass(frozen=True, slots=True)
class ProposedAction:
    """An action suggested for an incident, awaiting authorisation and approval."""

    id: str
    incident_id: str
    kind: ActionKind
    target: str
    reason: str
    proposed_by: str

    def __post_init__(self) -> None:
        """Reject blank ids, target, reason or proposer."""
        for name in ("id", "incident_id", "target", "reason", "proposed_by"):
            require_text(getattr(self, name), name)

    @property
    def impact(self) -> Impact:
        """Impact comes from the catalogue, never from the proposer."""
        return CATALOGUE[self.kind].impact


@dataclass(frozen=True, slots=True)
class ApprovalRequirement:
    """Who must approve an action and how many distinct people."""

    role: str
    count: int


def approval_requirement(kind: ActionKind, severity: Severity) -> ApprovalRequirement:
    """Return the approval an action needs; HIGH impact on a CRITICAL incident needs two."""
    impact = CATALOGUE[kind].impact
    two_person = impact is Impact.HIGH and severity is Severity.CRITICAL
    return ApprovalRequirement(role=APPROVER_ROLE[impact], count=2 if two_person else 1)


def target_of(kind: ActionKind, entities: Entities) -> str | None:
    """Return the entity value the action would act on, if the incident names one."""
    return entities.present().get(CATALOGUE[kind].target_entity)


def parse_action_kind(value: str) -> ActionKind:
    """Return the catalogue entry for ``value`` (e.g. an LLM suggestion).

    Raises:
        UnknownActionError: If ``value`` is not exactly a catalogue value.
    """
    try:
        return ActionKind(value)
    except ValueError as exc:
        raise UnknownActionError(f"{value!r} is not an allow-listed action") from exc
