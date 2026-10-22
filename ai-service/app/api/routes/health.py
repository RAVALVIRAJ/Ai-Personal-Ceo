from fastapi import APIRouter


router = APIRouter(
    prefix="/api/v1",
    tags=["Health"],
)


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai-service",
    }