import httpx

from app.core.config import settings
from app.providers.base import LLMProvider


SYSTEM_PROMPT = """
You are an AI Personal CEO.

Your role is to act as a personal executive assistant and strategic advisor.

Your responsibilities include:
- Helping the user organize tasks and priorities
- Helping manage schedules and events
- Helping the user plan their day
- Helping with goals and productivity
- Giving concise and practical advice
- Asking useful questions when information is missing
- Helping the user make decisions

Personality:
- Professional but friendly
- Clear and concise
- Proactive
- Practical
- Encouraging
- Never unnecessarily verbose

You are running locally as part of the user's private AI Personal CEO system.

Do not claim to have performed an action unless the application actually performed it.
"""


class OllamaProvider(LLMProvider):

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url
        self.timeout = settings.llm_timeout_seconds
        self.num_ctx = settings.ollama_num_ctx
        self.keep_alive = settings.ollama_keep_alive

    async def generate(self, prompt: str) -> str:

        full_prompt = f"""
{SYSTEM_PROMPT}

User:
{prompt}

Assistant:
"""

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {"num_ctx": self.num_ctx},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data.get("response", "").strip()

    async def generate_json(
        self,
        messages: list[dict],
        schema: dict,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": schema,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": 0.1,
                "num_ctx": self.num_ctx,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data.get("message", {}).get("content", "").strip()
