import asyncio
import time
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(
    prefix="/api/v1/status",
    tags=["Service Status"],
)

_openai_cache_duration_seconds = 30
_openai_status_checked_at = 0.0
_openai_status_online = False
_openai_status_lock = asyncio.Lock()


async def check_backend() -> dict[str, bool | int | None]:
    url = f"{settings.backend_url.rstrip('/')}/actuator/health"
    try:
        async with httpx.AsyncClient(
            timeout=settings.status_timeout_seconds
        ) as client:
            response = await client.get(url)
        return {
            "online": response.status_code == 200,
            "status_code": response.status_code,
        }
    except httpx.HTTPError:
        return {"online": False, "status_code": None}


async def check_ollama() -> dict[str, bool | str]:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(
            timeout=settings.status_timeout_seconds
        ) as client:
            response = await client.get(url)
        if response.status_code != 200:
            return {
                "online": False,
                "model_available": False,
                "model": settings.ollama_model,
            }

        models = response.json().get("models", [])
        names = [item.get("name", "") for item in models]
        available = any(
            name == settings.ollama_model
            or name.startswith(f"{settings.ollama_model}:")
            for name in names
        )
        return {
            "online": True,
            "model_available": available,
            "model": settings.ollama_model,
        }
    except (httpx.HTTPError, ValueError):
        return {
            "online": False,
            "model_available": False,
            "model": settings.ollama_model,
        }


async def check_openai() -> bool:
    global _openai_status_checked_at, _openai_status_online

    if not settings.openai_api_key.strip():
        return False

    now = time.monotonic()
    if now - _openai_status_checked_at < _openai_cache_duration_seconds:
        return _openai_status_online

    async with _openai_status_lock:
        now = time.monotonic()
        if now - _openai_status_checked_at < _openai_cache_duration_seconds:
            return _openai_status_online

        base_url = (
            settings.openai_base_url or "https://api.openai.com/v1"
        ).rstrip("/")
        try:
            async with httpx.AsyncClient(
                timeout=settings.status_timeout_seconds
            ) as client:
                response = await client.get(
                    f"{base_url}/models",
                    headers={
                        "Authorization": f"Bearer {settings.openai_api_key}"
                    },
                )
            _openai_status_online = response.is_success
        except httpx.HTTPError:
            _openai_status_online = False

        _openai_status_checked_at = time.monotonic()
        return _openai_status_online


def get_openai_label() -> str:
    base_url = settings.openai_base_url or "https://api.openai.com/v1"
    hostname = (urlparse(base_url).hostname or "").lower()
    if hostname.endswith("groq.com"):
        return "Groq (cloud)"
    if hostname.endswith("openrouter.ai"):
        return "OpenRouter (cloud)"
    if hostname == "api.openai.com":
        return "OpenAI (cloud)"
    return "Cloud LLM"


@router.get("/services")
async def get_service_status() -> dict:
    backend = await check_backend()
    configured_provider = settings.llm_provider.lower().strip()

    if configured_provider == "ollama":
        ollama = await check_ollama()
        llm = {
            "provider": "ollama",
            "label": "Ollama (local)",
            "model": settings.ollama_model,
            "online": bool(ollama["online"] and ollama["model_available"]),
            "fallback_provider": settings.llm_fallback_provider or None,
        }
        ollama_status: dict[str, bool | str | None] = {
            **ollama,
            "applicable": True,
        }
    else:
        llm_online = (
            await check_openai()
            if configured_provider in {"openai", "groq", "openrouter"}
            else False
        )
        llm = {
            "provider": "openai",
            "label": get_openai_label(),
            "model": settings.openai_model,
            "online": llm_online,
            "fallback_provider": settings.llm_fallback_provider or None,
        }
        ollama_status = {"online": None, "applicable": False}

    services = {
        "ai_service": {"online": True},
        "backend": backend,
        "ollama": ollama_status,
    }
    all_online = (
        services["ai_service"]["online"]
        and backend["online"]
        and llm["online"]
    )

    return {
        "overall": "ONLINE" if all_online else "DEGRADED",
        "mode": settings.app_mode,
        "llm": llm,
        "services": services,
    }
