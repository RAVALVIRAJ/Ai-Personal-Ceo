from app.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):

    async def generate(self, prompt: str) -> str:
        return "Mock provider response"

    async def generate_json(
        self,
        messages: list[dict],
        schema: dict,
    ) -> str:
        return "{}"
