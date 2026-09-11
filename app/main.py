from fastapi import FastAPI

from app.api.routes import chat, health
from app.config import get_settings
from app.core.cors import setup_cors

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Bek (Oybek Ismanov) portfolio RAG chat API",
)

setup_cors(app, settings)
app.include_router(health.router)
app.include_router(chat.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "chat": "POST /api/chat",
    }
