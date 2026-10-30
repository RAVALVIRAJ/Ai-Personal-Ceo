import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure ai-service root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException

from app.api.routes.chat import chat
from app.core.config import settings
from app.providers.base import LLMProvider
from app.routers.llm_options import get_options
from app.schemas.chat import ChatRequest
from app.services.ai_service import AIService


class DummyProvider(LLMProvider):
    async def generate(self, prompt: str) -> str:
        return "Dummy text response"

    async def generate_json(self, messages: list[dict], schema: dict) -> str:
        return "{}"


class TestLLMOptionsEndpoint(unittest.TestCase):
    def test_options_local_no_openai_key(self):
        with patch.object(settings, "app_mode", "local"), \
             patch.object(settings, "openai_api_key", ""):
            data = get_options()
            self.assertEqual(data, {"providers": ["ollama"]})

    def test_options_local_with_openai_key(self):
        with patch.object(settings, "app_mode", "local"), \
             patch.object(settings, "openai_api_key", "sk-mock-key"):
            data = get_options()
            self.assertEqual(data, {"providers": ["ollama", "openai"]})

    def test_options_live_with_openai_key(self):
        with patch.object(settings, "app_mode", "live"), \
             patch.object(settings, "openai_api_key", "sk-mock-key"):
            data = get_options()
            self.assertEqual(data, {"providers": ["openai"]})

    def test_options_live_no_openai_key(self):
        with patch.object(settings, "app_mode", "live"), \
             patch.object(settings, "openai_api_key", ""):
            data = get_options()
            self.assertEqual(data, {"providers": []})


class TestChatRequestSchema(unittest.TestCase):
    def test_chat_request_default_provider_is_none(self):
        req = ChatRequest(message="Hello")
        self.assertIsNone(req.provider)

    def test_chat_request_explicit_provider(self):
        req = ChatRequest(message="Hello", provider="ollama")
        self.assertEqual(req.provider, "ollama")

        req2 = ChatRequest(message="Hello", provider="openai")
        self.assertEqual(req2.provider, "openai")


class TestProviderValidation(unittest.TestCase):
    def test_invalid_provider_raises_400(self):
        ai = AIService(provider=DummyProvider())
        with patch.object(settings, "app_mode", "local"), \
             patch.object(settings, "openai_api_key", ""):
            req = ChatRequest(message="test message", provider="invalid_llm")
            coro = ai.process_message(req)
            try:
                with self.assertRaises(HTTPException) as ctx:
                    coro.send(None)
                self.assertEqual(ctx.exception.status_code, 400)
                self.assertIn("invalid_llm", ctx.exception.detail)
            finally:
                coro.close()

    def test_unconfigured_openai_provider_raises_400_in_local_without_key(self):
        ai = AIService(provider=DummyProvider())
        with patch.object(settings, "app_mode", "local"), \
             patch.object(settings, "openai_api_key", ""):
            req = ChatRequest(message="test message", provider="openai")
            coro = ai.process_message(req)
            try:
                with self.assertRaises(HTTPException) as ctx:
                    coro.send(None)
                self.assertEqual(ctx.exception.status_code, 400)
                self.assertIn("openai", ctx.exception.detail)
            finally:
                coro.close()

    def test_valid_provider_switches_provider(self):
        ai = AIService(provider=DummyProvider())
        with patch.object(settings, "app_mode", "local"), \
             patch.object(settings, "openai_api_key", "sk-mock-key"), \
             patch("app.services.ai_service.get_provider") as mock_get_provider:
            mock_llm = DummyProvider()
            mock_get_provider.return_value = mock_llm

            req = ChatRequest(message="hello", provider="openai")
            coro = ai.process_message(req)
            try:
                coro.send(None)
            except Exception:
                pass
            finally:
                coro.close()

            mock_get_provider.assert_called_with("openai")
            self.assertEqual(ai.provider, mock_llm)

    def test_chat_route_provider_validation(self):
        with patch.object(settings, "app_mode", "local"), \
             patch.object(settings, "openai_api_key", ""):
            req = ChatRequest(message="hello", provider="unknown_provider")
            coro = chat(req)
            try:
                with self.assertRaises(HTTPException) as ctx:
                    coro.send(None)
                self.assertEqual(ctx.exception.status_code, 400)
            finally:
                coro.close()


if __name__ == "__main__":
    unittest.main()
