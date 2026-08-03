# Aria — Voice AI Platform

Production platform for persistent realtime voice agents across web, mobile, and desktop.

| Phase | Status |
| --- | --- |
| 1 Auth + LiveKit + OpenAI Realtime | Done |
| 2 Memory + tools + Postgres/Redis/pgvector | Done |
| 3 Knowledge graph + MCP + proactive jobs | Done |
| 4 Mobile + desktop + analytics + multi-agent | Done |

## Architecture docs

- [Phase 1](docs/PHASE_1_ARCHITECTURE.md)
- [Phase 2](docs/PHASE_2_ARCHITECTURE.md)
- [Phase 3](docs/PHASE_3_ARCHITECTURE.md)
- [Phase 4](docs/PHASE_4_ARCHITECTURE.md)

## Apps

```text
apps/web       Next.js client (talk, memory, analytics)
apps/api       FastAPI control plane
apps/agent     LiveKit realtime worker
apps/worker    Proactive reminder runner
apps/mobile    Expo mobile client
apps/desktop   Electron desktop shell
```

## Quick start

```bash
cp .env.example .env
cp .env.example apps/web/.env.local

# Data plane
docker compose up -d postgres redis

# API
cd apps/api
source .venv/bin/activate  # or: uv venv && uv pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Agent
cd apps/agent && pip install -e ".[dev]" && python -m voice_agent.main start

# Web
cd apps/web && npm install && npm run dev
```

## Tests

```bash
# API
cd apps/api && . .venv/bin/activate && pytest

# Agent
cd apps/agent && . .venv/bin/activate && pytest

# Web
cd apps/web && npm test && npm run typecheck && npm run build

# Mobile / desktop contract tests
cd apps/mobile && npm test
cd apps/desktop && npm test
```

## Key APIs

- Voice: `POST /v1/voice/sessions`
- Memory: `/v1/memory/*`
- Tools: `/v1/tools`, `/v1/tools/invoke`
- Graph: `/v1/graph/*`
- Reminders: `/v1/reminders`
- Analytics: `/v1/analytics/summary`
- Multi-agent route: `POST /v1/agents/route`
