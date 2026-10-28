"""The action catalogue: the only containment actions the system can ever execute.

Data, not logic. Adding an action means adding a row here and a test; nothing an
LLM says can create a new one.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class ActionKind(StrEnum):
    """An allow-listed containment action."""

    BLOCK_IP = "block_ip"
    FORCE_MFA_RESET = "force_mfa_reset"
    PURGE_EMAIL = "purge_email"
    RESET_PASSWORD = "reset_password"  # noqa: S105 -- action name, not a secret
    DISABLE_USER = "disable_user"
    REVOKE_ACCESS_KEY = "revoke_access_key"
    ISOLATE_HOST = "isolate_host"


class Impact(StrEnum):
    """How disruptive an action is; decides who must approve it."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ActionSpec:
    """Catalogue row: which entity the action targets and how disruptive it is."""

    target_entity: str
    impact: Impact


CATALOGUE: Mapping[ActionKind, ActionSpec] = MappingProxyType(
    {
        ActionKind.BLOCK_IP: ActionSpec("ip", Impact.LOW),
        ActionKind.FORCE_MFA_RESET: ActionSpec("user", Impact.LOW),
        ActionKind.PURGE_EMAIL: ActionSpec("email_id", Impact.MEDIUM),
        ActionKind.RESET_PASSWORD: ActionSpec("user", Impact.MEDIUM),
        ActionKind.DISABLE_USER: ActionSpec("user", Impact.HIGH),
        ActionKind.REVOKE_ACCESS_KEY: ActionSpec("access_key_id", Impact.HIGH),
        ActionKind.ISOLATE_HOST: ActionSpec("host", Impact.HIGH),
    }
)

APPROVER_ROLE: Mapping[Impact, str] = MappingProxyType(
    {
        Impact.LOW: "soc-analyst-l2",
        Impact.MEDIUM: "soc-analyst-l2",
        Impact.HIGH: "incident-commander",
    }
)
