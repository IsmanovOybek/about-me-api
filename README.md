# about-me-api

Bek / 베크 (Ismanov Oybek) portfolio uchun FastAPI RAG chat backend.

Frontend (`about-me` Next.js) shu API’ga ulanadi:

- `POST /api/chat`
- `GET /health`
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Stack

- FastAPI + Uvicorn + Pydantic v2
- Custom RAG pipeline
- Embeddings: OpenAI yoki local (`BAAI/bge-m3`)
- Vector DB: Chroma (lokal) — `VectorStore` protokoli orqali keyin Qdrant/pgvector ga oson o‘tish mumkin
- LLM: OpenAI / Anthropic / Ollama (env orqali)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` ichida kamida `OPENAI_API_KEY` ni to‘ldiring (default provider `openai`).

Local embeddings uchun:

```env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-m3
```

## Knowledge ingest

Corpus: `app/data/knowledge/corpus.json`

```bash
python scripts/ingest_knowledge.py
```

Bu script documentlarni embed qilib `storage/chroma` ga yozadi.

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Docs: http://localhost:8000/docs

## API contract

### Health

`GET /health`

```json
{ "status": "ok" }
```

### Chat

`POST /api/chat`

Request:

```json
{
  "message": "What projects has Bek built?",
  "locale": "en"
}
```

`locale`: `en` | `ko` | `ru` | `uz` (default `en`)

Response:

```json
{
  "reply": "..."
}
```

Validation:

- bo‘sh `message` → `422`
- juda uzun `message` → `400`

## RAG flow

1. User message keladi
2. Message embed qilinadi
3. Chroma’dan top-k relevant chunk olinadi
4. System prompt + context + question LLM’ga beriladi
5. Javob faqat corpus asosida, tanlangan locale’da qaytadi

## Project layout

```text
app/
  main.py
  config.py
  api/routes/     # health, chat
  schemas/        # request/response models
  services/       # rag, embeddings, llm, ingest
  data/knowledge/ # corpus
  core/           # cors
scripts/
  ingest_knowledge.py
```

## Frontend ulash

Frontend env:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Response contract o‘zgarmaydi: har doim `{ "reply": "string" }`.
