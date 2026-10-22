import logging

from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.mock import MockLLMProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


def get_provider() -> LLMProvider:
    """
    Factory function returning the configured LLMProvider based on core/config.py settings.
    Supported modes:
      - 'ollama': Local Ollama service using OLLAMA_BASE_URL and OLLAMA_MODEL.
      - 'openai': OpenAI or OpenAI-compatible service (Groq, OpenRouter) using
                  OPENAI_API_KEY, OPENAI_BASE_URL, and OPENAI_MODEL.
      - 'mock': MockLLMProvider for unit testing without network dependencies.
    """
    provider_name = (settings.llm_provider or "ollama").lower().strip()

    if provider_name == "ollama":
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )
    elif provider_name in ("openai", "groq", "openrouter"):
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )
    elif provider_name == "mock":
        return MockLLMProvider()
    else:
        logger.warning(
            f"Unknown LLM_PROVIDER '{provider_name}'. Defaulting to OllamaProvider."
        )
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )


__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "MockLLMProvider",
    "get_provider",
]
