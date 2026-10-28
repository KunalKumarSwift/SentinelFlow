"""Interface to a large language model that returns schema-validated output.

Prompts keep untrusted data (alert text, log lines) in a separate field so every
provider renders it inside explicit delimiters, never mixed into instructions.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class Prompt:
    """A structured prompt.

    Attributes:
        name: Stable id such as ``"triage.classify"``; used for tracing and test scripts.
        untrusted: Attacker-influenced values, rendered as data only.
    """

    name: str
    system: str
    instructions: str
    untrusted: Mapping[str, str] = field(default_factory=dict[str, str])


class LLMProvider(Protocol):
    """A model that answers a prompt with an instance of a Pydantic schema."""

    def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> T:
        """Return the model's answer parsed as ``schema``.

        Raises:
            ProviderError: If the model is unreachable or its output does not fit ``schema``.
        """
        ...
