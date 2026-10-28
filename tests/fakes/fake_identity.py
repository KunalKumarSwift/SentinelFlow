"""Recording identity-provider fake for tests."""

from collections.abc import Iterable

from sentinelflow.domain.actions import ActionResult, ProposedAction
from sentinelflow.domain.enrichment import UserContext


class FakeIdentityProvider:
    """In-memory directory that remembers which users were looked up."""

    def __init__(self, users: Iterable[UserContext]) -> None:
        """Serve ``users``; everyone else is unknown."""
        self._by_id = {user.user_id: user for user in users}
        self.lookups: list[str] = []
        self.applied: list[ProposedAction] = []
        self._results: dict[str, ActionResult] = {}

    def lookup_user(self, user_id: str) -> UserContext | None:
        """Record the lookup and return the stored context, if any."""
        self.lookups.append(user_id)
        return self._by_id.get(user_id)

    def apply(self, action: ProposedAction, idempotency_key: str) -> ActionResult:
        """Record the action once per key and report success."""
        if idempotency_key not in self._results:
            self.applied.append(action)
            self._results[idempotency_key] = ActionResult(action.id, True, "applied")
        return self._results[idempotency_key]
