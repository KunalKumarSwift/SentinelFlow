"""Scripted LLM for tests: deterministic, free, and records every prompt."""

from collections.abc import Mapping

from pydantic import BaseModel, ValidationError

from sentinelflow.contracts.llm import Prompt
from sentinelflow.domain.errors import ProviderError

Script = Mapping[str, Mapping[str, object] | Exception]


class FakeLLM:
    """Answers each prompt by name from a script of raw outputs or exceptions.

    A raw output that does not fit the requested schema raises ``ProviderError``,
    exactly like a real provider receiving malformed model output.
    """

    def __init__(self, script: Script) -> None:
        """Answer prompt ``name`` with ``script[name]``."""
        self._script = script
        self.prompts: list[Prompt] = []

    def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> T:
        """Record the prompt and return the scripted output parsed as ``schema``."""
        self.prompts.append(prompt)
        answer = self._script[prompt.name]
        if isinstance(answer, Exception):
            raise answer
        try:
            return schema.model_validate(answer)
        except ValidationError as exc:
            raise ProviderError("model output did not match schema", retryable=False) from exc
