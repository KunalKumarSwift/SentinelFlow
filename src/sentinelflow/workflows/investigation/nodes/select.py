"""Selection node: validate the LLM's choices against candidates and the playbook.

The LLM can only narrow: techniques must be retrieved candidates, actions must be in the
rule's playbook and have a target. Everything else is dropped and reported.
"""

from sentinelflow.domain.actions import ActionKind, ProposedAction, parse_action_kind, target_of
from sentinelflow.domain.attack import AttackTechnique
from sentinelflow.domain.errors import UnknownActionError
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.investigation import InvestigationResult
from sentinelflow.domain.playbooks import playbook_for
from sentinelflow.security.system_principals import ORCHESTRATOR_SUBJECT
from sentinelflow.workflows.investigation.schema import InvestigationAnalysis
from sentinelflow.workflows.investigation.state import InvestigationUpdate, SelectInput

UNAVAILABLE = "LLM analysis unavailable; proposing the rule's playbook for human approval."


def select(state: SelectInput) -> InvestigationUpdate:
    """Produce the validated ``InvestigationResult``."""
    analysis, rule_id = state["analysis"], state["alert"].rule_id
    techniques, dropped_t = _techniques(state["candidates"], analysis)
    kinds, dropped_k = _kinds(playbook_for(rule_id), analysis)
    actions, dropped_a = _actions(state["incident"], kinds, rule_id)
    narrative = UNAVAILABLE if analysis is None else analysis.narrative
    dropped = (*dropped_t, *dropped_k, *dropped_a)
    return {
        "result": InvestigationResult(state["timeline"], techniques, actions, narrative, dropped)
    }


def _techniques(
    candidates: tuple[AttackTechnique, ...], analysis: InvestigationAnalysis | None
) -> tuple[tuple[AttackTechnique, ...], list[str]]:
    if analysis is None:
        return (), []
    known = {t.technique_id for t in candidates}
    chosen = tuple(t for t in candidates if t.technique_id in analysis.technique_ids)
    return chosen, [f"technique:{i}" for i in analysis.technique_ids if i not in known]


def _kinds(
    playbook: tuple[ActionKind, ...], analysis: InvestigationAnalysis | None
) -> tuple[list[ActionKind], list[str]]:
    if analysis is None:
        return list(playbook), []
    kinds: list[ActionKind] = []
    dropped: list[str] = []
    for value in analysis.suggested_actions:
        kind = _parse(value)
        if kind is None or kind not in playbook:
            dropped.append(f"action:{value}")
        elif kind not in kinds:
            kinds.append(kind)
    return kinds, dropped


def _parse(value: str) -> ActionKind | None:
    try:
        return parse_action_kind(value)
    except UnknownActionError:
        return None


def _actions(
    incident: Incident, kinds: list[ActionKind], rule_id: str
) -> tuple[tuple[ProposedAction, ...], list[str]]:
    actions: list[ProposedAction] = []
    dropped: list[str] = []
    for kind in kinds:
        target = target_of(kind, incident.entities)
        if target is None:
            dropped.append(f"action:{kind.value}")
            continue
        reason = f"playbook for {rule_id}"
        actions.append(
            ProposedAction(
                f"{incident.id}:{kind.value}",
                incident.id,
                kind,
                target,
                reason,
                ORCHESTRATOR_SUBJECT,
            )
        )
    return tuple(actions), dropped
