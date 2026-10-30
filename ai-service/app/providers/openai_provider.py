import logging
from openai import AsyncOpenAI

from app.core.config import settings
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    Provider for OpenAI and OpenAI-compatible APIs (such as Groq, OpenRouter, Together, etc.).
    Supports custom base_url and API keys configured via settings or constructor arguments.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.base_url = base_url if base_url is not None else settings.openai_base_url
        self.model = model if model is not None else settings.openai_model

        client_kwargs = {
            "api_key": self.api_key or "no-key-provided",
            "timeout": settings.llm_timeout_seconds,
        }
        if self.base_url and self.base_url.strip():
            client_kwargs["base_url"] = self.base_url.strip()

        self.client = AsyncOpenAI(**client_kwargs)

    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return (response.choices[0].message.content or "").strip()

    async def generate_json(
        self,
        messages: list[dict],
        schema: dict,
    ) -> str:
        # First attempt with json_schema structured output; fallback to json_object for providers
        # (like older Groq models) that do not yet support the full json_schema spec.
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "extracted_item",
                        "schema": schema,
                    },
                },
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.info(
                f"json_schema response_format not accepted by provider ({exc}); falling back to json_object."
            )
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return (response.choices[0].message.content or "").strip()
