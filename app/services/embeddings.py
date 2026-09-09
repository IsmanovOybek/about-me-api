from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Sequence

from app.config import Settings, get_settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError


class OpenAIEmbeddings(EmbeddingProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
            )
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(
            model=self._model,
            input=list(texts),
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class LocalEmbeddings(EmbeddingProvider):
    """Local embeddings via sentence-transformers (e.g. BAAI/bge-m3)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def build_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    cfg = settings or get_settings()
    if cfg.embedding_provider == "openai":
        return OpenAIEmbeddings(
            api_key=cfg.openai_api_key,
            model=cfg.embedding_model,
        )
    if cfg.embedding_provider == "local":
        model = cfg.embedding_model
        if model == "text-embedding-3-small":
            model = "BAAI/bge-m3"
        return LocalEmbeddings(model_name=model)
    raise RuntimeError(f"Unsupported embedding provider: {cfg.embedding_provider}")


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return build_embedding_provider()
