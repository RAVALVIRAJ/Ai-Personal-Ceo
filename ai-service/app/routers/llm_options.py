from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/api/v1/llm/options")
def get_options():
    """Return the list of available LLM providers based on environment config."""
    providers = []
    if settings.app_mode == "local":
        providers.append("ollama")
    if settings.openai_api_key:
        providers.append("openai")
    return {"providers": providers}
