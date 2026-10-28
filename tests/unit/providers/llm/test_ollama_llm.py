"""Tests for the Ollama provider (no network)."""

import httpx
import ollama
import pytest

from sentinelflow.contracts.llm import Prompt
from sentinelflow.providers.llm.ollama_llm import OllamaLLM, is_retryable
from tests.unit.providers.llm.test_invoke import Answer, StubChat

REQUEST = httpx.Request("POST", "http://localhost:11434/api/chat")


def test_default_chat_model_targets_configured_server() -> None:
    chat = OllamaLLM(model="qwen2.5:7b", base_url="http://ollama:11434").chat_model()
    assert (chat.model, chat.base_url) == ("qwen2.5:7b", "http://ollama:11434")


def test_structured_uses_injected_chat_model() -> None:
    llm = OllamaLLM("m", "http://x", chat=StubChat(Answer(value=3)))
    assert llm.structured(Prompt("p", "S", "I"), Answer) == Answer(value=3)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (httpx.ConnectError("refused", request=REQUEST), True),
        (httpx.ReadTimeout("slow", request=REQUEST), True),
        (ollama.ResponseError("overloaded", status_code=503), True),
        (ollama.ResponseError("model not found", status_code=404), False),
        (ValueError("bad output"), False),
    ],
)
def test_error_classification(exc: Exception, expected: bool) -> None:
    assert is_retryable(exc) is expected
