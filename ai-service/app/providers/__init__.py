import logging

from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.mock import MockLLMProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


def get_provider(provider_name: str | None = None) -> LLMProvider:
    name = (provider_name or settings.llm_provider or "ollama").lower().strip()

    if name == "ollama":
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )
    if name in {"openai", "groq", "openrouter"}:
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )
    if name == "mock":
        return MockLLMProvider()

    logger.warning("Unknown LLM provider '%s'; using Ollama.", name)
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
