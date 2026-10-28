"""Low-cost hosted LLM: Claude Haiku via the Anthropic API (through LangChain).

``temperature`` is deliberately left unset: current API versions reject sampling
parameters, and structured output does not need them.
"""

import anthropic
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, SecretStr

from sentinelflow.contracts.llm import Prompt
from sentinelflow.providers.llm._invoke import StructuredChat, invoke_structured

MAX_TOKENS = 1024
TIMEOUT_SECONDS = 60.0


class AnthropicLLM:
    """``LLMProvider`` backed by Claude."""

    def __init__(self, model: str, api_key: str, chat: StructuredChat | None = None) -> None:
        """Configure the model; ``chat`` lets tests inject a stand-in chat model."""
        self._model, self._api_key, self._chat = model, SecretStr(api_key), chat

    def chat_model(self) -> ChatAnthropic:
        """Return a LangChain chat model for Claude (no network call)."""
        # Alias names, because pyright sees pydantic aliases as the constructor parameters.
        return ChatAnthropic(
            model_name=self._model,
            api_key=self._api_key,
            max_tokens_to_sample=MAX_TOKENS,
            timeout=TIMEOUT_SECONDS,
            stop=None,
        )

    def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> T:
        """Answer ``prompt`` as ``schema`` (see ``LLMProvider``)."""
        chat = self._chat or self.chat_model()
        return invoke_structured(chat, prompt, schema, is_retryable)


def is_retryable(exc: Exception) -> bool:
    """Rate limits, connection problems and 5xx are retryable; other API errors are not."""
    if isinstance(exc, anthropic.RateLimitError | anthropic.APIConnectionError):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        return exc.status_code >= 500
    return False
