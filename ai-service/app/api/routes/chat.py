from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import ai_service


router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI"],
)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await ai_service.process_message(request)