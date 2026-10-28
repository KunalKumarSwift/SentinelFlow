"""Retrieve candidate ATT&CK techniques by keyword overlap.

Phase 2 uses transparent keyword retrieval; the LLM may only choose among these
candidates, so it cannot invent technique ids. A vector index can replace this later
behind the same function.
"""

from collections.abc import Iterable

from sentinelflow.domain.attack_table import TECHNIQUES, AttackTechnique

__all__ = ["TECHNIQUES", "AttackTechnique", "candidate_techniques"]


def candidate_techniques(
    rule_id: str, event_kinds: Iterable[str], limit: int = 5
) -> tuple[AttackTechnique, ...]:
    """Return up to ``limit`` techniques sharing keywords with the rule or event kinds.

    Ranked by number of shared keywords, then technique id.
    """
    tokens = _tokens([rule_id, *event_kinds])
    scored = [(len(tokens & set(t.keywords)), t) for t in TECHNIQUES]
    ranked = sorted((s for s in scored if s[0] > 0), key=lambda s: (-s[0], s[1].technique_id))
    return tuple(t for _, t in ranked[:limit])


def _tokens(words: Iterable[str]) -> set[str]:
    lowered = [w.lower() for w in words]
    return set(lowered) | {part for w in lowered for part in w.split("_")}
