"""Tests for MITRE ATT&CK candidate retrieval."""

from sentinelflow.domain.attack import TECHNIQUES, candidate_techniques


def test_brute_force_signals_rank_t1110_first() -> None:
    found = candidate_techniques("brute_force_success", ["login_failed", "login_succeeded"])
    assert found[0].technique_id == "T1110"
    assert "T1078" in {t.technique_id for t in found}


def test_unrelated_signals_find_nothing() -> None:
    assert candidate_techniques("dormant_account", ["printer_jam"]) == ()


def test_at_most_limit_candidates_are_returned() -> None:
    kinds = [kw for t in TECHNIQUES for kw in t.keywords]
    assert len(candidate_techniques("x", kinds, limit=3)) == 3


def test_every_technique_has_id_name_tactic_and_keywords() -> None:
    assert all(
        t.technique_id.startswith("T") and t.name and t.tactic and t.keywords for t in TECHNIQUES
    )
