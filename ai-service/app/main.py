import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.routes import chat, health
from app.routers import llm_options
from app.routers.status import router as status_router


_chat_requests_by_client: defaultdict[str, deque[float]] = defaultdict(deque)

app = FastAPI(
    title="AI Personal Manager",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def limit_chat_requests(request: Request, call_next):
    limit = settings.rate_limit_per_minute
    if (
        limit <= 0
        or request.method != "POST"
        or request.url.path != "/api/v1/ai/chat"
    ):
        return await call_next(request)

    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = (
        forwarded_for.split(",", maxsplit=1)[0].strip()
        if forwarded_for
        else request.client.host if request.client else "unknown"
    )
    request_times = _chat_requests_by_client[client_ip or "unknown"]
    now = time.monotonic()

    while request_times and now - request_times[0] >= 60:
        request_times.popleft()

    if len(request_times) >= limit:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many messages. Please wait a moment."},
        )

    request_times.append(now)
    return await call_next(request)


app.include_router(status_router)
app.include_router(health.router)
app.include_router(llm_options.router)
app.include_router(chat.router)
