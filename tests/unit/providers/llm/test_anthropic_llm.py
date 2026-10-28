"""Tests for the Claude (Anthropic) provider (no network)."""

import anthropic
import httpx2
import pytest

from sentinelflow.contracts.llm import Prompt
from sentinelflow.providers.llm.anthropic_llm import AnthropicLLM, is_retryable
from tests.unit.providers.llm.test_invoke import Answer, StubChat

# The Anthropic SDK 2.x is built on httpx2, so its errors need httpx2 objects.
REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
KEY = "sk-ant-test-" + "x" * 20


def _status(code: int) -> httpx2.Response:
    return httpx2.Response(code, request=REQUEST)


def test_default_chat_model_uses_given_model_and_hides_key() -> None:
    chat = AnthropicLLM(model="claude-haiku-5-5", api_key=KEY).chat_model()
    assert (chat.model, chat.max_tokens, chat.default_request_timeout) == (
        "claude-haiku-5-5",
        1024,
        60.0,
    )
    assert KEY not in repr(chat)


def test_structured_uses_injected_chat_model() -> None:
    llm = AnthropicLLM("claude-haiku-5-5", KEY, chat=StubChat(Answer(value=4)))
    assert llm.structured(Prompt("p", "S", "I"), Answer) == Answer(value=4)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (anthropic.RateLimitError("slow down", response=_status(429), body=None), True),
        (anthropic.InternalServerError("oops", response=_status(500), body=None), True),
        (anthropic.APIConnectionError(request=REQUEST), True),
        (anthropic.BadRequestError("bad", response=_status(400), body=None), False),
        (anthropic.AuthenticationError("key", response=_status(401), body=None), False),
        (ValueError("bad output"), False),
    ],
)
def test_error_classification(exc: Exception, expected: bool) -> None:
    assert is_retryable(exc) is expected
