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

## Deploy

Production image `requirements-prod.txt` ishlatadi (OpenAI embeddings; local `sentence-transformers` yo‘q — image engil).

### Muhim env

| Key | Misol |
| --- | --- |
| `OPENAI_API_KEY` | `sk-...` |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app,http://localhost:3000` |
| `TELEGRAM_BOT_TOKEN` | optional |
| `TELEGRAM_CHAT_ID` | optional |
| `INGEST_ON_START` | `if-empty` (default) / `always` / `never` |
| `CHROMA_DIR` | `/app/storage/chroma` |
| `PORT` | platform beradi (Render/Railway) |

Frontend:

```env
NEXT_PUBLIC_API_URL=https://your-api-url
```

### Lokal Docker

```bash
cp .env.example .env
# .env ni to‘ldiring
docker compose up --build
```

Health: http://localhost:8000/health

Corpus yangilanganda:

```bash
docker compose exec api python scripts/ingest_knowledge.py
```

### Render

1. Repo’ni Render’ga ulang
2. `render.yaml` ishlatiladi (Docker + disk volume)
3. Dashboard’da `OPENAI_API_KEY`, `CORS_ORIGINS`, Telegram env’larni qo‘ying

### Railway

1. New project → Deploy from GitHub
2. `railway.json` Dockerfile build ishlatadi
3. Variables: `OPENAI_API_KEY`, `CORS_ORIGINS`, ...
4. Volume mount: `/app/storage/chroma` (tavsiya)

### VPS (oddiy)

```bash
docker build -t about-me-api .
docker run -d --name about-me-api \
  -p 8000:8000 \
  --env-file .env \
  -e CHROMA_DIR=/app/storage/chroma \
  -v about_me_chroma:/app/storage/chroma \
  about-me-api
```

### Deploy checklist

1. `.env` / platform secrets to‘ldirilgan
2. `CORS_ORIGINS` da frontend production URL bor
3. Birinchi start’da ingest o‘tadi (`INGEST_ON_START=if-empty`)
4. `GET /health` → `ok`
5. `POST /api/chat` ishlaydi
6. Frontend `NEXT_PUBLIC_API_URL` production API’ga ulangan
