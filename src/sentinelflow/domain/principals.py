"""Who is acting: a human user or a service account, with tenant, team and roles."""

from dataclasses import dataclass
from enum import StrEnum

from sentinelflow.domain._validation import require_text


class PrincipalKind(StrEnum):
    """Whether a principal is a person or a machine identity."""

    USER = "user"
    SERVICE = "service"


@dataclass(frozen=True, slots=True)
class Principal:
    """An authenticated identity, built from a verified token.

    Attributes:
        subject: Stable unique id of the user or service account.
        roles: Role names; unknown roles grant nothing (default deny).
    """

    subject: str
    tenant_id: str
    team: str
    roles: frozenset[str]
    kind: PrincipalKind = PrincipalKind.USER

    def __post_init__(self) -> None:
        """Reject blank subject or tenant."""
        require_text(self.subject, "subject")
        require_text(self.tenant_id, "tenant_id")
