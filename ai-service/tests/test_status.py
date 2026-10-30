import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import _chat_requests_by_client, app
from app.routers.status import get_service_status


class ServiceStatusTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_status_does_not_require_ollama(self):
        with (
            patch.object(settings, "llm_provider", "openai"),
            patch.object(settings, "openai_base_url", "https://api.groq.com/openai/v1"),
            patch.object(settings, "openai_model", "test-model"),
            patch.object(settings, "app_mode", "live"),
            patch("app.routers.status.check_backend", new_callable=AsyncMock) as backend,
            patch("app.routers.status.check_openai", new_callable=AsyncMock) as openai,
            patch("app.routers.status.check_ollama", new_callable=AsyncMock) as ollama,
        ):
            backend.return_value = {"online": True, "status_code": 200}
            openai.return_value = True
            response = await get_service_status()

        self.assertEqual(response["overall"], "ONLINE")
        self.assertEqual(response["mode"], "live")
        self.assertEqual(response["llm"]["label"], "Groq (cloud)")
        self.assertEqual(response["llm"]["model"], "test-model")
        self.assertTrue(response["llm"]["online"])
        self.assertEqual(
            response["services"]["ollama"],
            {"online": None, "applicable": False},
        )
        ollama.assert_not_awaited()

    async def test_ollama_status_includes_model_availability(self):
        with (
            patch.object(settings, "llm_provider", "ollama"),
            patch.object(settings, "ollama_model", "test-model"),
            patch.object(settings, "app_mode", "local"),
            patch("app.routers.status.check_backend", new_callable=AsyncMock) as backend,
            patch("app.routers.status.check_ollama", new_callable=AsyncMock) as ollama,
        ):
            backend.return_value = {"online": True, "status_code": 200}
            ollama.return_value = {
                "online": True,
                "model_available": True,
                "model": "test-model",
            }
            response = await get_service_status()

        self.assertEqual(response["overall"], "ONLINE")
        self.assertEqual(response["llm"]["label"], "Ollama (local)")
        self.assertTrue(response["llm"]["online"])
        self.assertTrue(response["services"]["ollama"]["applicable"])

    def test_chat_rate_limit_can_be_disabled_or_enforced(self):
        _chat_requests_by_client.clear()
        with patch.object(settings, "rate_limit_per_minute", 1):
            with TestClient(app) as client:
                first = client.post(
                    "/api/v1/ai/chat",
                    json={"message": "hello", "provider": "unavailable"},
                )
                second = client.post(
                    "/api/v1/ai/chat",
                    json={"message": "hello", "provider": "unavailable"},
                )

        self.assertEqual(first.status_code, 400)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(
            second.json(),
            {"detail": "Too many messages. Please wait a moment."},
        )
        _chat_requests_by_client.clear()
