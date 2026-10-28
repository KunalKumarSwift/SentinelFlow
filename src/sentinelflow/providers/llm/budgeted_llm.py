"""``BudgetedLLM``: a decorator that charges every call to the tenant's daily budget.

Workflows are unchanged (open/closed): when the budget is spent the decorator raises
``BudgetExceededError``, a permanent ``ProviderError``, and every LLM step already fails
safe on that: triage → NEEDS_REVIEW, investigation → playbook defaults, report → facts.
"""

from pydantic import BaseModel

from sentinelflow.contracts.llm import LLMProvider, Prompt
from sentinelflow.contracts.metrics import Metrics
from sentinelflow.contracts.token_budget import TokenBudget
from sentinelflow.domain.errors import BudgetExceededError
from sentinelflow.providers.metrics.null_metrics import NullMetrics

# Charged up front for the answer, so a call can never push a tenant far past its limit.
OUTPUT_ALLOWANCE = 1024
UNATTRIBUTED = "unattributed"


def estimate_tokens(prompt: Prompt) -> int:
    """Estimate a call's tokens: ~4 characters per prompt token plus the output allowance."""
    chars = len(prompt.system) + len(prompt.instructions)
    chars += sum(len(value) for value in prompt.untrusted.values())
    return chars // 4 + OUTPUT_ALLOWANCE


class BudgetedLLM:
    """Wraps an ``LLMProvider``; refuses calls once the tenant's budget is used up."""

    def __init__(
        self,
        inner: LLMProvider,
        budget: TokenBudget,
        daily_limit: int,
        metrics: Metrics | None = None,
    ) -> None:
        """Charge calls to ``inner`` against ``budget`` (``daily_limit`` tokens per tenant)."""
        self._inner, self._budget, self._limit = inner, budget, daily_limit
        self._metrics = metrics or NullMetrics()

    def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> T:
        """Reserve the estimated tokens, then delegate.

        Raises:
            BudgetExceededError: If the tenant has no budget left today.
        """
        tenant, tokens = prompt.tenant_id or UNATTRIBUTED, estimate_tokens(prompt)
        if not self._budget.try_spend(tenant, tokens, self._limit):
            raise BudgetExceededError(f"daily LLM token budget used up for tenant {tenant}")
        self._metrics.llm_tokens(tenant, tokens)
        return self._inner.structured(prompt, schema)
