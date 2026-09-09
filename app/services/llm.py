from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from app.config import Settings, get_settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class OpenAILLM(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0.4,
            max_tokens=900,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        return (content or "").strip()


class AnthropicLLM(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=800,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()


class OllamaLLM(LLMProvider):
    def __init__(self, base_url: str, model: str) -> None:
        import httpx

        self._base_url = base_url.rstrip("/")
        self._model = model
        self._http = httpx.Client(timeout=120.0)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._http.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        return str(data.get("message", {}).get("content", "")).strip()


def build_llm_provider(settings: Settings | None = None) -> LLMProvider:
    cfg = settings or get_settings()
    if cfg.llm_provider == "openai":
        return OpenAILLM(api_key=cfg.openai_api_key, model=cfg.llm_model)
    if cfg.llm_provider == "anthropic":
        return AnthropicLLM(api_key=cfg.anthropic_api_key, model=cfg.llm_model)
    if cfg.llm_provider == "ollama":
        return OllamaLLM(base_url=cfg.ollama_base_url, model=cfg.llm_model)
    raise RuntimeError(f"Unsupported LLM provider: {cfg.llm_provider}")


@lru_cache
def get_llm_provider() -> LLMProvider:
    return build_llm_provider()
