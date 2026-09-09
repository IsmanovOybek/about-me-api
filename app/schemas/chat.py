from typing import Literal

from pydantic import BaseModel, Field, field_validator

Locale = Literal["en", "ko", "ru", "uz"]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    locale: Locale = "en"

    @field_validator("message")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message cannot be empty")
        return cleaned


class ChatResponse(BaseModel):
    reply: str


class HealthResponse(BaseModel):
    status: str
