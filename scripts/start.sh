#!/usr/bin/env sh
set -eu

MODE="${INGEST_ON_START:-if-empty}"

case "$MODE" in
  always)
    echo "[start] Ingesting knowledge (always)..."
    python scripts/ingest_knowledge.py
    ;;
  if-empty)
    echo "[start] Ingesting knowledge if collection is empty..."
    python scripts/ingest_knowledge.py --if-empty
    ;;
  never)
    echo "[start] Skipping ingest (INGEST_ON_START=never)"
    ;;
  *)
    echo "[start] Unknown INGEST_ON_START=$MODE (use always|if-empty|never)"
    exit 1
    ;;
esac

PORT="${PORT:-8000}"
echo "[start] Starting uvicorn on 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
