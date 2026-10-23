from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(prefix="/api/v1/llm", tags=["LLM"])


@router.get("/options")
async def get_llm_options() -> dict[str, object]:
    providers: list[str] = []

    if settings.app_mode.lower() == "local":
        providers.append("ollama")
    if settings.openai_api_key.strip():
        providers.append("openai")

    return {
        "providers": providers,
        "default": settings.llm_provider,
    }
