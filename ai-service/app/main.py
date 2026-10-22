import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.status import router as status_router
from app.api.routes import chat, health


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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router)
app.include_router(health.router)
app.include_router(chat.router)