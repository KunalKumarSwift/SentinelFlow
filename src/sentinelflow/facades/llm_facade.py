"""Choose the LLM provider from settings. Switch logic only.

Provider modules are imported inside their branch so an unused backend's library
is never loaded.
"""

from sentinelflow.contracts.llm import LLMProvider
from sentinelflow.core.config import Settings

DEFAULT_MODELS = {"ollama": "qwen2.5:7b", "anthropic": "claude-haiku-5-5"}


def make_llm(settings: Settings) -> LLMProvider:
    """Return the configured ``LLMProvider``."""
    match settings.llm_backend:
        case "ollama":
            from sentinelflow.providers.llm.ollama_llm import OllamaLLM

            return OllamaLLM(settings.llm_model or DEFAULT_MODELS["ollama"], settings.ollama_url)
        case "anthropic":
            from sentinelflow.providers.llm.anthropic_llm import AnthropicLLM

            key = settings.anthropic_api_key
            secret = "" if key is None else key.get_secret_value()
            return AnthropicLLM(settings.llm_model or DEFAULT_MODELS["anthropic"], secret)
        case _:  # "none"
            from sentinelflow.providers.llm.disabled_llm import DisabledLLM

            return DisabledLLM()
