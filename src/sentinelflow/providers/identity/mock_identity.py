"""User directory served from in-memory data, e.g. a simulator scenario's seed data."""

from collections.abc import Iterable

from sentinelflow.domain.actions import ActionResult, ProposedAction
from sentinelflow.domain.enrichment import UserContext


class MockIdentity:
    """Answers user lookups from a fixed directory."""

    def __init__(self, users: Iterable[UserContext]) -> None:
        """Index ``users`` by user id."""
        self._by_id = {user.user_id: user for user in users}
        self._results: dict[str, ActionResult] = {}

    def lookup_user(self, user_id: str) -> UserContext | None:
        """Return the stored context for ``user_id``, or ``None`` if unknown."""
        return self._by_id.get(user_id)

    def apply(self, action: ProposedAction, idempotency_key: str) -> ActionResult:
        """Pretend to apply ``action``; the same key always returns the same result."""
        if idempotency_key not in self._results:
            detail = f"{action.kind.value} applied to {action.target}"
            self._results[idempotency_key] = ActionResult(action.id, True, detail)
        return self._results[idempotency_key]
