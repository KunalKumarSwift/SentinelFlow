"""Per-rule containment playbooks: the most an investigation may propose for a rule.

Data, not logic. The LLM can only narrow a playbook, never extend it.
"""

from collections.abc import Mapping
from types import MappingProxyType

from sentinelflow.domain.actions_table import ActionKind as K

PLAYBOOKS: Mapping[str, tuple[K, ...]] = MappingProxyType(
    {
        "brute_force_success": (K.DISABLE_USER, K.BLOCK_IP),
        "impossible_travel": (K.FORCE_MFA_RESET,),
        "access_key_anomaly": (K.REVOKE_ACCESS_KEY,),
        "phishing_click": (K.PURGE_EMAIL, K.RESET_PASSWORD),
        "suspicious_process": (K.ISOLATE_HOST,),
        "large_download": (),
        "dormant_account": (),
        "over_privileged_account": (),
    }
)


def playbook_for(rule_id: str) -> tuple[K, ...]:
    """Return the allowed actions for ``rule_id`` (none for unknown rules)."""
    return PLAYBOOKS.get(rule_id, ())
