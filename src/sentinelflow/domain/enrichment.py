"""Context gathered during triage: threat intel about IPs and facts about users."""

from dataclasses import dataclass

from sentinelflow.domain.errors import InvalidValueError

MALICIOUS_SCORE = 80


@dataclass(frozen=True, slots=True)
class IpReputation:
    """Threat-intel verdict for one IP address.

    Attributes:
        score: 0 (clean) to 100 (known malicious).
    """

    ip: str
    score: int
    categories: tuple[str, ...] = ()
    country: str | None = None

    def __post_init__(self) -> None:
        """Reject scores outside 0-100."""
        if not 0 <= self.score <= 100:
            raise InvalidValueError(f"score must be between 0 and 100, got {self.score}")

    @property
    def is_malicious(self) -> bool:
        """Whether the score is high enough to treat the IP as hostile."""
        return self.score >= MALICIOUS_SCORE


@dataclass(frozen=True, slots=True)
class UserContext:
    """Directory facts about the user an incident involves."""

    user_id: str
    department: str | None = None
    is_privileged: bool = False
    mfa_enabled: bool = True
    usual_countries: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Enrichment:
    """Everything triage learned about an incident's entities; any part may be missing."""

    ip_reputation: IpReputation | None = None
    user: UserContext | None = None
