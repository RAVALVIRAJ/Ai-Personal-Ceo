import asyncio

import httpx
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(
    prefix="/api/v1/status",
    tags=["Service Status"],
)


SPRING_URL = f"{settings.backend_url.rstrip('/')}/api/v1/tasks"
OLLAMA_URL = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
OLLAMA_MODEL = settings.ollama_model


async def check_backend():
    try:
        async with httpx.AsyncClient(
            timeout=2.0
        ) as client:

            response = await client.get(
                SPRING_URL
            )

            return {
                "online":
                    response.status_code < 500,

                "status_code":
                    response.status_code,
            }

    except Exception:
        return {
            "online": False,
            "status_code": None,
        }


async def check_ollama():
    try:
        async with httpx.AsyncClient(
            timeout=2.0
        ) as client:

            response = await client.get(
                OLLAMA_URL
            )

            if response.status_code != 200:
                return {
                    "online": False,
                    "model_available": False,
                    "model": OLLAMA_MODEL,
                }

            data = response.json()

            models = data.get(
                "models",
                [],
            )

            model_names = [
                model.get("name", "")
                for model in models
            ]

            model_available = any(
                name == OLLAMA_MODEL
                or name.startswith(
                    f"{OLLAMA_MODEL}:"
                )
                for name in model_names
            )

            return {
                "online": True,
                "model_available":
                    model_available,
                "model":
                    OLLAMA_MODEL,
            }

    except Exception:
        return {
            "online": False,
            "model_available": False,
            "model": OLLAMA_MODEL,
        }


@router.get("/services")
async def get_service_status():

    backend, ollama = await asyncio.gather(
        check_backend(),
        check_ollama(),
    )

    all_online = (
        backend["online"]
        and ollama["online"]
    )

    return {
        "overall":
            "ONLINE"
            if all_online
            else "DEGRADED",

        "services": {
            "ai_service": {
                "online": True,
            },

            "backend": backend,

            "ollama": ollama,
        },
    }