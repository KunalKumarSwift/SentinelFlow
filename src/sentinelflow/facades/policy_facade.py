"""Choose the policy engine from settings. Switch logic only."""

from sentinelflow.core.config import Settings
from sentinelflow.security.opa_engine import OpaPolicyEngine
from sentinelflow.security.policy import PolicyEngine
from sentinelflow.security.policy_engine import InCodePolicyEngine


def make_policy_engine(settings: Settings) -> PolicyEngine:
    """Return the in-code engine, or the OPA client for ``POLICY_ENGINE=opa``."""
    if settings.policy_engine == "opa":
        return OpaPolicyEngine(settings.opa_url)
    return InCodePolicyEngine()
