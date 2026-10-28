"""Interface to the identity provider (user directory)."""

from typing import Protocol

from sentinelflow.domain.enrichment import UserContext


class IdentityProvider(Protocol):
    """Read access to directory facts about users."""

    def lookup_user(self, user_id: str) -> UserContext | None:
        """Return directory facts for ``user_id``, or ``None`` if no such user exists.

        Raises:
            ProviderError: If the directory cannot be reached (real providers only).
        """
        ...
