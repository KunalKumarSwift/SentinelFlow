"""Recording identity-provider fake for tests."""

from collections.abc import Iterable

from sentinelflow.domain.enrichment import UserContext


class FakeIdentityProvider:
    """In-memory directory that remembers which users were looked up."""

    def __init__(self, users: Iterable[UserContext]) -> None:
        """Serve ``users``; everyone else is unknown."""
        self._by_id = {user.user_id: user for user in users}
        self.lookups: list[str] = []

    def lookup_user(self, user_id: str) -> UserContext | None:
        """Record the lookup and return the stored context, if any."""
        self.lookups.append(user_id)
        return self._by_id.get(user_id)
