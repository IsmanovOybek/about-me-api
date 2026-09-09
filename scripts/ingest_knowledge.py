#!/usr/bin/env python3
"""Ingest portfolio knowledge into Chroma vector store."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.services.ingest import ingest_knowledge


def main() -> None:
    settings = get_settings()
    print(f"Knowledge dir: {settings.knowledge_path}")
    print(f"Chroma dir:    {settings.chroma_path}")
    print(f"Embeddings:    {settings.embedding_provider}/{settings.embedding_model}")
    count = ingest_knowledge(settings)
    print(f"Ingested {count} documents into collection '{settings.chroma_collection}'.")


if __name__ == "__main__":
    main()
