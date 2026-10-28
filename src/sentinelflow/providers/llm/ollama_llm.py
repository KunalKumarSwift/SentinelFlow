"""Local, free LLM via Ollama (default model ``qwen2.5:7b``)."""

import httpx
import ollama
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from sentinelflow.contracts.llm import Prompt
from sentinelflow.providers.llm._invoke import StructuredChat, invoke_structured


class OllamaLLM:
    """``LLMProvider`` backed by a local Ollama server."""

    def __init__(self, model: str, base_url: str, chat: StructuredChat | None = None) -> None:
        """Configure the model; ``chat`` lets tests inject a stand-in chat model."""
        self._model, self._base_url, self._chat = model, base_url, chat

    def chat_model(self) -> ChatOllama:
        """Return a LangChain chat model for the configured server (no network call)."""
        return ChatOllama(model=self._model, base_url=self._base_url)

    def structured[T: BaseModel](self, prompt: Prompt, schema: type[T]) -> T:
        """Answer ``prompt`` as ``schema`` (see ``LLMProvider``)."""
        chat = self._chat or self.chat_model()
        return invoke_structured(chat, prompt, schema, is_retryable)


def is_retryable(exc: Exception) -> bool:
    """Network trouble and server-side errors are worth retrying; the rest are not."""
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, ollama.ResponseError):
        return exc.status_code >= 500 or exc.status_code == 429
    return False
