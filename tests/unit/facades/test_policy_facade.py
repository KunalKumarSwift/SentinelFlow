"""In-code policy engine by default; OPA when configured."""

from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.policy_facade import make_policy_engine
from sentinelflow.security.opa_engine import OpaPolicyEngine
from sentinelflow.security.policy_engine import InCodePolicyEngine

SECRET = SecretStr("s" * 32)


def test_default_is_the_in_code_engine() -> None:
    assert isinstance(make_policy_engine(Settings(jwt_secret=SECRET)), InCodePolicyEngine)  # type: ignore[call-arg]


def test_opa_is_selected_by_setting() -> None:
    settings = Settings(jwt_secret=SECRET, policy_engine="opa")  # type: ignore[call-arg]
    assert isinstance(make_policy_engine(settings), OpaPolicyEngine)
