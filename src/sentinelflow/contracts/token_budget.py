"""Interface of the per-tenant daily LLM token budget."""

from typing import Protocol


class TokenBudget(Protocol):
    """Counts tokens per tenant per UTC day."""

    def try_spend(self, tenant_id: str, tokens: int, daily_limit: int) -> bool:
        """Reserve ``tokens`` for today if that stays within ``daily_limit``.

        Returns:
            ``True`` if reserved; ``False`` (and nothing reserved) if it would exceed.
        """
        ...
