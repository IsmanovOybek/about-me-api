FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    CHROMA_DIR=/app/storage/chroma

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

COPY app ./app
COPY scripts ./scripts
COPY storage/.gitkeep ./storage/.gitkeep

RUN chmod +x scripts/start.sh \
    && mkdir -p /app/storage/chroma

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT','8000') + '/health')"

CMD ["./scripts/start.sh"]
