from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response from the language model."""
        raise NotImplementedError

    @abstractmethod
    async def generate_json(
        self,
        messages: list[dict],
        schema: dict,
    ) -> str:
        """Generate a structured JSON response from the language model."""
        raise NotImplementedError
