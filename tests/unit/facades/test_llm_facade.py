"""Tests for choosing the LLM provider from settings."""

import pytest
from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.llm_facade import make_llm
from sentinelflow.providers.llm.anthropic_llm import AnthropicLLM
from sentinelflow.providers.llm.disabled_llm import DisabledLLM
from sentinelflow.providers.llm.ollama_llm import OllamaLLM

SECRET = SecretStr("s" * 32)
KEY = SecretStr("sk-ant-test-" + "x" * 20)


def _settings(**values: object) -> Settings:
    return Settings(jwt_secret=SECRET, **values)  # type: ignore[arg-type]


def test_none_backend_disables_the_llm() -> None:
    assert isinstance(make_llm(_settings()), DisabledLLM)


@pytest.mark.parametrize(
    ("values", "model"),
    [
        ({"llm_backend": "ollama"}, "qwen2.5:7b"),
        ({"llm_backend": "ollama", "llm_model": "llama3.1:8b"}, "llama3.1:8b"),
    ],
)
def test_ollama_backend(values: dict[str, object], model: str) -> None:
    llm = make_llm(_settings(**values))
    assert isinstance(llm, OllamaLLM) and llm.chat_model().model == model


def test_anthropic_backend_defaults_to_haiku() -> None:
    llm = make_llm(_settings(llm_backend="anthropic", anthropic_api_key=KEY))
    assert isinstance(llm, AnthropicLLM) and llm.chat_model().model == "claude-haiku-5-5"
