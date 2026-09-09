from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import Settings, get_settings
from app.services.embeddings import EmbeddingProvider, build_embedding_provider


@dataclass(frozen=True)
class KnowledgeDocument:
    id: str
    title: str
    tags: list[str]
    content: str
    locale: str | None = None

    @property
    def searchable_text(self) -> str:
        tags = ", ".join(self.tags)
        locale = f" Locale: {self.locale}." if self.locale else ""
        return f"Title: {self.title}. Tags: {tags}.{locale}\n{self.content}"


class VectorStore(Protocol):
    """Thin interface so Chroma can later be swapped for Qdrant/pgvector."""

    def reset_and_upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> int: ...

    def query(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]: ...


class ChromaVectorStore:
    def __init__(self, persist_dir: str, collection_name: str) -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection_name = collection_name
        self._collection = self._get_or_create()

    def _get_or_create(self) -> Collection:
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset_and_upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> int:
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:  # noqa: BLE001
            pass
        self._collection = self._get_or_create()
        if not ids:
            return 0
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(ids)

    def query(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        chunks: list[dict[str, Any]] = []
        for idx, doc in enumerate(docs):
            chunks.append(
                {
                    "id": ids[idx] if idx < len(ids) else "",
                    "document": doc,
                    "metadata": metas[idx] if idx < len(metas) else {},
                    "distance": distances[idx] if idx < len(distances) else None,
                }
            )
        return chunks


def load_knowledge_documents(knowledge_dir: str | Path) -> list[KnowledgeDocument]:
    root = Path(knowledge_dir)
    if not root.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {root}")

    documents: list[KnowledgeDocument] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".json":
            documents.extend(_load_json_file(path))
        elif path.suffix.lower() in {".md", ".txt"}:
            documents.append(_load_text_file(path))
    return documents


def _load_json_file(path: Path) -> list[KnowledgeDocument]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else [raw]
    docs: list[KnowledgeDocument] = []
    for item in items:
        docs.append(
            KnowledgeDocument(
                id=str(item["id"]),
                title=str(item["title"]),
                tags=[str(t) for t in item.get("tags", [])],
                content=str(item["content"]),
                locale=item.get("locale"),
            )
        )
    return docs


def _load_text_file(path: Path) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=path.stem,
        title=path.stem.replace("-", " ").replace("_", " ").title(),
        tags=["markdown"],
        content=path.read_text(encoding="utf-8"),
    )


def ingest_knowledge(
    settings: Settings | None = None,
    embeddings: EmbeddingProvider | None = None,
    store: VectorStore | None = None,
) -> int:
    cfg = settings or get_settings()
    embedder = embeddings or build_embedding_provider(cfg)

    docs = load_knowledge_documents(cfg.knowledge_path)
    if not docs:
        raise RuntimeError(f"No knowledge documents found in {cfg.knowledge_path}")

    if store is None:
        vector_store = ChromaVectorStore(cfg.chroma_path, cfg.chroma_collection)
    else:
        vector_store = store

    texts = [doc.searchable_text for doc in docs]
    vectors = embedder.embed_documents(texts)
    metadatas: list[dict[str, Any]] = [
        {
            "title": doc.title,
            "tags": ",".join(doc.tags),
            "locale": doc.locale or "",
        }
        for doc in docs
    ]
    return vector_store.reset_and_upsert(
        ids=[doc.id for doc in docs],
        documents=texts,
        embeddings=vectors,
        metadatas=metadatas,
    )
