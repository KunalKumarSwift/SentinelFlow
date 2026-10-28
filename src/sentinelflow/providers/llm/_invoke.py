"""Shared structured-output call used by every LangChain-backed provider.

All library exceptions are translated into ``ProviderError`` here, at the provider
boundary, so workflows never depend on Ollama or Anthropic exception types. Error
messages carry only the prompt name and exception class, never hosts or keys.
"""

from collections.abc import Callable
from typing import Literal, Protocol

from pydantic import BaseModel

from sentinelflow.contracts.llm import Prompt
from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.llm._render import render


class StructuredRunnable(Protocol):
    """The runnable a chat model returns from ``with_structured_output``."""

    def invoke(self, input: list[tuple[str, str]], /) -> object:
        """Run the model."""
        ...


class StructuredChat(Protocol):
    """The part of a LangChain chat model this project uses."""

    def with_structured_output(
        self, schema: type[BaseModel], *, method: Literal["json_schema"]
    ) -> StructuredRunnable:
        """Bind an output schema."""
        ...


def invoke_structured[T: BaseModel](
    chat: StructuredChat,
    prompt: Prompt,
    schema: type[T],
    is_retryable: Callable[[Exception], bool],
) -> T:
    """Ask ``chat`` for a ``schema`` instance answering ``prompt``.

    Raises:
        ProviderError: On any library failure (``retryable`` decided by ``is_retryable``)
            or when the output is not a ``schema`` instance (never retryable).
    """
    runnable = chat.with_structured_output(schema, method="json_schema")
    try:
        result = runnable.invoke(render(prompt))
    # Broad on purpose: every library failure is translated at this boundary.
    except Exception as exc:
        reason = f"{prompt.name}: {type(exc).__name__}"
        raise ProviderError(reason, retryable=is_retryable(exc)) from exc
    if not isinstance(result, schema):
        raise ProviderError(f"{prompt.name}: output did not match schema", retryable=False)
    return result
