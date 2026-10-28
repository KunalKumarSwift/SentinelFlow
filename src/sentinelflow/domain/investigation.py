"""Outcome of investigating an incident."""

from dataclasses import dataclass

from sentinelflow.domain.actions import ProposedAction
from sentinelflow.domain.attack import AttackTechnique
from sentinelflow.domain.timeline import TimelineEntry


@dataclass(frozen=True, slots=True)
class InvestigationResult:
    """Timeline, mapped techniques and proposed actions.

    Attributes:
        dropped: LLM suggestions rejected by validation, e.g. ``"action:drop_database"``.
    """

    timeline: tuple[TimelineEntry, ...]
    techniques: tuple[AttackTechnique, ...]
    actions: tuple[ProposedAction, ...]
    narrative: str
    dropped: tuple[str, ...] = ()
