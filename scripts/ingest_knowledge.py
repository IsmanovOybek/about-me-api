#!/usr/bin/env python3
"""Ingest portfolio knowledge into Chroma vector store."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.services.ingest import ChromaVectorStore, ingest_knowledge


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest portfolio knowledge")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="Skip ingest when the Chroma collection already has documents",
    )
    args = parser.parse_args()

    settings = get_settings()
    print(f"Knowledge dir: {settings.knowledge_path}")
    print(f"Chroma dir:    {settings.chroma_path}")
    print(f"Embeddings:    {settings.embedding_provider}/{settings.embedding_model}")

    store = ChromaVectorStore(settings.chroma_path, settings.chroma_collection)
    if args.if_empty and store.count() > 0:
        print(
            f"Collection '{settings.chroma_collection}' already has "
            f"{store.count()} documents — skipping ingest."
        )
        return

    count = ingest_knowledge(settings, store=store)
    print(f"Ingested {count} documents into collection '{settings.chroma_collection}'.")


if __name__ == "__main__":
    main()
