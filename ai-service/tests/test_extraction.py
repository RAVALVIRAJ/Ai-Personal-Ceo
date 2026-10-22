import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

from app.schemas.chat import ChatRequest, Intent
from app.core.config import settings
from app.providers import get_provider, LLMProvider, OllamaProvider, OpenAIProvider, MockLLMProvider
from app.services.extraction_service import (
    ExtractedItem,
    ExtractionService,
    build_extraction_system_prompt,
    resolve_date_and_time,
)
from app.services.ai_service import AIService


class MockProvider(LLMProvider):
    def __init__(self, json_responses=None):
        self.json_responses = json_responses or []
        self.call_count = 0

    async def generate(self, prompt: str) -> str:
        return "Mock text response"

    async def generate_json(self, messages: list[dict], schema: dict) -> str:
        resp = self.json_responses[self.call_count]
        self.call_count += 1
        return resp


class TestLLMExtraction(unittest.IsolatedAsyncioTestCase):

    def test_ollama_provider_methods(self):
        ollama = OllamaProvider()
        self.assertTrue(hasattr(ollama, "generate_json"))
        self.assertTrue(hasattr(ollama, "generate"))

    def test_extracted_item_schema(self):
        fields = set(ExtractedItem.model_fields.keys())
        expected = {
            "intent",
            "title",
            "date_phrase",
            "time_phrase",
            "duration_minutes",
            "priority",
            "missing_fields",
        }
        self.assertEqual(fields, expected)

    def test_system_prompt(self):
        prompt = build_extraction_system_prompt()
        self.assertIn("Asia/Kolkata", prompt)
        self.assertIn("Current Date:", prompt)
        self.assertIn("Current Weekday:", prompt)
        self.assertIn("Current Time:", prompt)
        self.assertIn("Example 1 (Relative date / time)", prompt)
        self.assertIn("Example 2 (Weekday)", prompt)
        self.assertIn("Example 3 (Missing time)", prompt)
        self.assertIn("Example 4 (Duration)", prompt)
        self.assertIn("Example 5 (Event with start and end time)", prompt)
        self.assertIn("Example 6 (Message with no actionable intent)", prompt)

    def test_date_and_time_resolution(self):
        # 1. Weekday + time
        d1, t1, e1 = resolve_date_and_time("next Friday", "5pm")
        self.assertIsNotNone(d1)
        self.assertEqual(t1, "17:00")

        # 2. Date + named time of day
        d2, t2, e2 = resolve_date_and_time("3rd Nov", "evening")
        self.assertEqual(d2, "2026-11-03")
        self.assertEqual(t2, "18:00")

        # 3. Relative time phrase with no date phrase
        d3, t3, e3 = resolve_date_and_time(None, "in 2 hours")
        self.assertIsNotNone(d3)
        self.assertIsNotNone(t3)

        # 4. Time range
        d4, t4, e4 = resolve_date_and_time("tomorrow", "3pm to 4pm")
        self.assertIsNotNone(d4)
        self.assertEqual(t4, "15:00")
        self.assertEqual(e4, "16:00")

        # 5. Start time + duration
        d5, t5, e5 = resolve_date_and_time("tomorrow", "4pm", duration_minutes=120)
        self.assertEqual(t5, "16:00")
        self.assertEqual(e5, "18:00")

    async def test_extraction_retry_and_fallback(self):
        # Successful on first attempt
        p1 = MockProvider([
            json.dumps({
                "intent": "CREATE_TASK",
                "title": "Clean kitchen",
                "date_phrase": "tomorrow",
                "time_phrase": "10am",
            })
        ])
        svc1 = ExtractionService(p1)
        res1 = await svc1.extract("clean kitchen tomorrow at 10am")
        self.assertIsNotNone(res1)
        self.assertEqual(res1.title, "Clean kitchen")
        self.assertEqual(p1.call_count, 1)

        # Invalid JSON first attempt, successful on retry
        p2 = MockProvider([
            "INVALID_JSON_HERE",
            json.dumps({
                "intent": "CREATE_TASK",
                "title": "Clean kitchen retry",
                "date_phrase": "tomorrow",
                "time_phrase": "10am",
            }),
        ])
        svc2 = ExtractionService(p2)
        res2 = await svc2.extract("clean kitchen tomorrow at 10am")
        self.assertIsNotNone(res2)
        self.assertEqual(res2.title, "Clean kitchen retry")
        self.assertEqual(p2.call_count, 2)

        # Invalid JSON on both attempts -> returns None for fallback
        p3 = MockProvider(["BAD_JSON_1", "BAD_JSON_2"])
        svc3 = ExtractionService(p3)
        res3 = await svc3.extract("clean kitchen tomorrow at 10am")
        self.assertIsNone(res3)
        self.assertEqual(p3.call_count, 2)

    async def test_explicit_commands_keep_regex_path(self):
        # Explicit complete task
        with patch("app.services.ai_service.backend_client.complete_task", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = {"id": 17, "status": "COMPLETED"}
            ai = AIService(provider=MockProvider([]))
            resp = await ai.process_message(ChatRequest(message="complete task 17"))
            self.assertEqual(resp.intent, Intent.COMPLETE_TASK)
            self.assertEqual(resp.task_id, 17)
            mock_complete.assert_called_once_with(17)

        # Explicit delete event
        with patch("app.services.ai_service.backend_client.get_event", new_callable=AsyncMock) as mock_get_evt, \
             patch("app.services.ai_service.backend_client.delete_event", new_callable=AsyncMock) as mock_del_evt:
            mock_get_evt.return_value = {"id": 5, "title": "Dentist"}
            mock_del_evt.return_value = {"success": True}
            ai = AIService(provider=MockProvider([]))
            resp = await ai.process_message(ChatRequest(message="delete event 5"))
            self.assertEqual(resp.intent, Intent.DELETE_EVENT)
            mock_del_evt.assert_called_once_with(5)

    async def test_ai_service_llm_task_creation(self):
        with patch("app.services.ai_service.backend_client.create_task", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": 42, "title": "Submit report"}
            llm_payload = json.dumps({
                "intent": "CREATE_TASK",
                "title": "Submit report",
                "date_phrase": "next Friday",
                "time_phrase": "5pm",
            })
            ai = AIService(provider=MockProvider([llm_payload]))
            resp = await ai.process_message(ChatRequest(message="remind me next Friday at 5 to submit report"))
            self.assertEqual(resp.intent, Intent.CREATE_TASK)
            self.assertEqual(resp.task_id, 42)
            self.assertEqual(resp.task.time, "17:00")
            mock_create.assert_called_once()

    async def test_ai_service_regex_fallback_when_extraction_fails(self):
        with patch("app.services.ai_service.backend_client.create_task", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": 99, "title": "Study math"}
            # Mock provider returns invalid JSON twice
            ai = AIService(provider=MockProvider(["BROKEN_JSON", "STILL_BROKEN"]))
            resp = await ai.process_message(ChatRequest(message="study math tomorrow at 6 PM"))
            self.assertEqual(resp.intent, Intent.CREATE_TASK)
            self.assertEqual(resp.task_id, 99)
            mock_create.assert_called_once()


    def test_get_provider_factory(self):
        # 1. Ollama mode
        with patch.object(settings, "llm_provider", "ollama"), \
             patch.object(settings, "ollama_model", "custom-model"), \
             patch.object(settings, "ollama_base_url", "http://localhost:11434"):
            provider = get_provider()
            self.assertIsInstance(provider, OllamaProvider)
            self.assertEqual(provider.model, "custom-model")
            self.assertEqual(provider.base_url, "http://localhost:11434")

        # 2. Mock mode
        with patch.object(settings, "llm_provider", "mock"):
            provider = get_provider()
            self.assertIsInstance(provider, MockLLMProvider)

        # 3. OpenAI-compatible mode (e.g. Groq / OpenRouter)
        with patch.object(settings, "llm_provider", "openai"), \
             patch.object(settings, "openai_api_key", "test-key-123"), \
             patch.object(settings, "openai_base_url", "https://api.groq.com/openai/v1"), \
             patch.object(settings, "openai_model", "llama-3.3-70b-versatile"):
            provider = get_provider()
            self.assertIsInstance(provider, OpenAIProvider)
            self.assertEqual(provider.model, "llama-3.3-70b-versatile")
            self.assertEqual(provider.base_url, "https://api.groq.com/openai/v1")
            self.assertEqual(provider.api_key, "test-key-123")
            self.assertEqual(str(provider.client.base_url), "https://api.groq.com/openai/v1/")

    def test_openai_provider_custom_base_url(self):
        # OpenRouter configuration test
        p = OpenAIProvider(
            api_key="sk-or-test",
            base_url="https://openrouter.ai/api/v1",
            model="meta-llama/llama-3.2-3b-instruct",
        )
        self.assertEqual(p.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(p.model, "meta-llama/llama-3.2-3b-instruct")
        self.assertEqual(str(p.client.base_url), "https://openrouter.ai/api/v1/")


if __name__ == "__main__":
    unittest.main()
