from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "about-me-api"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    llm_provider: Literal["openai", "anthropic", "ollama"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "gpt-4o-mini"

    embedding_provider: Literal["openai", "local"] = "openai"
    embedding_model: str = "text-embedding-3-small"

    chroma_dir: str = str(BASE_DIR / "storage" / "chroma")
    chroma_collection: str = "portfolio_knowledge"
    top_k: int = 6

    knowledge_dir: str = str(BASE_DIR / "app" / "data" / "knowledge")
    max_message_length: int = Field(default=2000, ge=100)

    # Website chat → Telegram notify (owner inbox)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def chroma_path(self) -> str:
        path = Path(self.chroma_dir)
        if not path.is_absolute():
            path = BASE_DIR / path
        return str(path.resolve())

    @property
    def knowledge_path(self) -> str:
        path = Path(self.knowledge_dir)
        if not path.is_absolute():
            path = BASE_DIR / path
        return str(path.resolve())


@lru_cache
def get_settings() -> Settings:
    return Settings()
