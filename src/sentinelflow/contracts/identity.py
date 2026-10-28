"""Interface to the identity provider (user directory)."""

from typing import Protocol

from sentinelflow.domain.actions import ActionResult, ProposedAction
from sentinelflow.domain.enrichment import UserContext


class IdentityProvider(Protocol):
    """Directory lookups plus the containment actions an identity system can apply."""

    def lookup_user(self, user_id: str) -> UserContext | None:
        """Return directory facts for ``user_id``, or ``None`` if no such user exists.

        Raises:
            ProviderError: If the directory cannot be reached (real providers only).
        """
        ...

    def apply(self, action: ProposedAction, idempotency_key: str) -> ActionResult:
        """Apply an approved action; repeating ``idempotency_key`` returns the first result.

        Raises:
            ProviderError: If the identity system cannot be reached (real providers only).
        """
        ...
