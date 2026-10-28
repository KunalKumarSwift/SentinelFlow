"""Tests for the shared structured-invocation helper."""

import pytest
from pydantic import BaseModel

from sentinelflow.contracts.llm import Prompt
from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.llm._invoke import invoke_structured

PROMPT = Prompt("triage.classify", "SYS", "DO", {"k": "v"})


class Answer(BaseModel):
    value: int


class StubChat:
    """Minimal stand-in for a LangChain chat model."""

    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[tuple[type[BaseModel], str, list[tuple[str, str]]]] = []

    def with_structured_output(self, schema: type[BaseModel], *, method: str) -> "StubChat":
        self.calls.append((schema, method, []))
        return self

    def invoke(self, messages: list[tuple[str, str]]) -> object:
        self.calls[-1][2].extend(messages)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_returns_parsed_answer_using_json_schema_mode() -> None:
    chat = StubChat(Answer(value=1))
    assert invoke_structured(chat, PROMPT, Answer, lambda _: True) == Answer(value=1)
    schema, method, messages = chat.calls[0]
    assert (schema, method, messages[0]) == (Answer, "json_schema", ("system", "SYS"))


def test_non_matching_output_is_a_permanent_provider_error() -> None:
    with pytest.raises(ProviderError) as info:
        invoke_structured(StubChat({"value": "x"}), PROMPT, Answer, lambda _: True)
    assert info.value.retryable is False


@pytest.mark.parametrize("retryable", [True, False])
def test_library_errors_are_classified(retryable: bool) -> None:
    chat = StubChat(ConnectionError("secret-host:11434 refused"))
    with pytest.raises(ProviderError, match=r"triage\.classify: ConnectionError") as info:
        invoke_structured(chat, PROMPT, Answer, lambda _: retryable)
    assert info.value.retryable is retryable
    assert "secret-host" not in str(info.value)
