"""``LLM_BACKEND=none``: no model at all.

Every call fails permanently, which the triage graph already treats as "send to a
human". The platform stays fully usable offline without pretending to classify.
"""

from pydantic import BaseModel

from sentinelflow.contracts.llm import Prompt
from sentinelflow.domain.errors import ProviderError


class DisabledLLM:
    """``LLMProvider`` that never answers."""

    def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> T:
        """Raise a non-retryable ``ProviderError``."""
        raise ProviderError(f"{prompt.name}: no LLM configured", retryable=False)
