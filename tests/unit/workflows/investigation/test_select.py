"""The LLM may only narrow the playbook and pick candidate techniques."""

from sentinelflow.domain.actions import ActionKind as K
from sentinelflow.domain.attack import candidate_techniques
from sentinelflow.domain.investigation import InvestigationResult
from sentinelflow.workflows.investigation.nodes.select import select
from sentinelflow.workflows.investigation.schema import InvestigationAnalysis
from sentinelflow.workflows.investigation.state import SelectInput
from tests.builders import an_alert, an_incident, some_entities


def _select(analysis: InvestigationAnalysis | None, **entity_changes: str | None) -> SelectInput:
    entities = some_entities(**entity_changes)
    return {
        "incident": an_incident(entities=entities),
        "alert": an_alert(entities=entities),
        "timeline": (),
        "candidates": candidate_techniques("brute_force_success", ["login_failed"]),
        "analysis": analysis,
    }


def _analysis(techniques: list[str], actions: list[str]) -> InvestigationAnalysis:
    return InvestigationAnalysis(narrative="n", technique_ids=techniques, suggested_actions=actions)


def _result(state: SelectInput) -> InvestigationResult:
    result = select(state).get("result")
    assert result is not None
    return result


def test_without_llm_the_playbook_defaults_are_proposed() -> None:
    result = _result(_select(None))
    assert [(a.kind, a.target) for a in result.actions] == [
        (K.DISABLE_USER, "alice"),
        (K.BLOCK_IP, "203.0.113.9"),
    ]
    assert result.techniques == () and "unavailable" in result.narrative


def test_llm_can_narrow_the_playbook() -> None:
    result = _result(_select(_analysis(["T1110"], ["block_ip"])))
    assert [a.kind for a in result.actions] == [K.BLOCK_IP]
    assert [t.technique_id for t in result.techniques] == ["T1110"]


def test_invented_or_off_playbook_items_are_dropped_and_reported() -> None:
    analysis = _analysis(["T1110", "T9999"], ["drop_database", "isolate_host", "block_ip"])
    result = _result(_select(analysis))
    assert [a.kind for a in result.actions] == [K.BLOCK_IP]
    assert set(result.dropped) == {"technique:T9999", "action:drop_database", "action:isolate_host"}


def test_action_without_a_target_is_dropped() -> None:
    result = _result(_select(None, ip=None))
    assert [a.kind for a in result.actions] == [K.DISABLE_USER]
    assert "action:block_ip" in result.dropped


def test_proposed_actions_have_incident_scoped_ids_and_orchestrator_proposer() -> None:
    action = _result(_select(None)).actions[0]
    assert (action.id, action.incident_id, action.proposed_by) == (
        "inc-0001:disable_user",
        "inc-0001",
        "svc-orchestrator",
    )


def test_repeated_suggestions_count_once() -> None:
    result = _result(_select(_analysis([], ["block_ip", "block_ip"])))
    assert [a.kind for a in result.actions] == [K.BLOCK_IP] and result.dropped == ()
