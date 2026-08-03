# Voice AI API

Control plane for authentication, LiveKit tokens, memory, and tools.

## Run locally

```bash
# Start Postgres + Redis from repo root
docker compose up -d postgres redis

cd apps/api
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `POST /v1/voice/sessions`
- `POST /v1/memory/items`
- `POST /v1/memory/search`
- `GET /v1/memory/bundle`
- `POST /v1/memory/conversations`
- `POST /v1/memory/turns`
- `GET /v1/tools`
- `POST /v1/tools/invoke`
