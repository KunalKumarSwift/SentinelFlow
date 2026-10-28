"""The OPA role data is generated from ``security/roles.py`` and must not drift."""

from scripts.gen_opa_data import TARGET, render


def test_committed_opa_data_matches_the_role_matrix() -> None:
    assert TARGET.read_text(encoding="utf-8") == render(), "run scripts/gen_opa_data.py"
