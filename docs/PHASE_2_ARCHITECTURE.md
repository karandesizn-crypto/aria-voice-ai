# Phase 2 Architecture

## Goal

Add durable intelligence around the Phase 1 voice path:

- Structured long-term memory (not raw transcript dumps alone)
- Tool framework with permissions, schemas, retries, and telemetry
- PostgreSQL + pgvector for persistence and semantic retrieval
- Redis for hot session context and tool rate limits

Knowledge graph, MCP, and Temporal remain Phase 3.

## System diagram

```text
┌────────────┐   JWT    ┌─────────────────────────────────────────┐
│  Web /     │ ───────▶ │  FastAPI control plane                  │
│  Agent     │          │  auth · voice tokens · memory · tools   │
└────────────┘          └───────────────┬─────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              PostgreSQL            Redis              OpenAI
              + pgvector         session ctx         embeddings
              memories           rate limits         (memory only)
              turns / prefs      tool locks
```

Voice media path is unchanged: WebRTC → LiveKit → OpenAI Realtime.

## Layer ownership

| Concern | Owner | Notes |
| --- | --- | --- |
| Schema + migrations | `apps/api` | Alembic is the source of truth |
| Memory write/read HTTP | `apps/api` | Clerk JWT for users; service key for agent |
| Tool execution HTTP | `apps/api` | Permission checks before invoke |
| Agent realtime tools | `apps/agent` | `function_tool` wrappers → API client |
| Hot context | Redis | Recent turns + retrieved memory bundle |
| Cold memory | Postgres | Episodic / semantic / preference rows + vectors |

## Design decisions

### 1. API owns persistence; agent calls the API

**Decision:** The agent does not open Postgres connections. It uses an internal HTTP client with `AGENT_SERVICE_TOKEN`.

**Why:** One security boundary, one migration path, no DB credentials on the media worker. Matches Phase 1 control/media split.

**Tradeoff:** Extra hop on tool calls (~tens of ms). Acceptable for tools; memory context is loaded at session start and refreshed, not on every audio frame.

### 2. Structured memories over transcript-only storage

**Decision:** Persist three memory kinds plus conversation turns:

- `episodic` — time-bound events (“user mentioned a Friday deadline”)
- `semantic` — durable facts (“prefers metric units”)
- `preference` — explicit settings
- `conversation_turns` — raw turns for audit and later extraction

**Why:** Retrieval quality collapses if everything is undifferentiated transcript chunks.

**Tradeoff:** Needs extraction logic (rules + LLM). Phase 2 ships write/read/search + a simple extractor; richer graph linking is Phase 3.

### 3. pgvector + embedding provider interface

**Decision:** `text-embedding-3-small` (1536 dims) behind `EmbeddingProvider`. Cosine distance via `<=>`.

**Why:** Good quality/cost default; interface allows swapping Voyage/others later.

**Tradeoff:** Vendor embedding lock-in until a second provider is added. Vectors are not portable across models without re-embed.

### 4. Memory scoring and deduplication

**Decision:** Each memory has `content_hash`, `importance` (0–1), `access_count`, `last_accessed_at`. Dedup on `(user_id, kind, content_hash)`. Retrieval score = similarity × importance × recency decay.

**Why:** Prevents near-duplicate preference spam and keeps top-k useful under voice context budgets.

### 5. Tool framework before OAuth-heavy integrations

**Decision:** Full tool contract now; implement:

- **Live:** Weather, Maps (HTTP providers with API keys or graceful mock fallback)
- **Scaffolded:** Calendar, Email, GitHub, Figma, Notion, Drive, Slack, Home Assistant

Each tool declares `name`, `capabilities`, JSON schema, `required_permissions`, retry policy, and emits structured telemetry.

**Why:** Wiring ten OAuth apps blocks the platform. The contract is the product; providers fill in later (and via MCP in Phase 3).

### 6. Redis is hot path only

**Decision:** Redis holds session conversation windows and per-user tool rate-limit counters. Not a source of truth.

**Why:** Postgres remains durable. Redis outage degrades cache, not memory integrity.

## Security

- All memory/tool routes require Clerk JWT (user) or agent service token (machine).
- Tools check `required_permissions` against a per-user grant table (defaults deny for scaffolded OAuth tools; weather/maps allow for authenticated users).
- Agent service token is a high-entropy secret, rotated via env; never shipped to the browser.
- No tool may receive raw DB credentials.
- PII in logs: log memory/tool IDs and kinds, not full memory bodies at INFO.

## Scalability

- Stateless API replicas behind a load balancer.
- Postgres: indexes on `(user_id, kind)`, HNSW/IVFFlat on embeddings, hash unique for dedup.
- Redis: key TTL for session windows; rate-limit keys expire naturally.
- Agent workers remain horizontally scalable; memory load is per-session burst, not per-audio-frame.

## Explicitly out of scope (Phase 2)

- Knowledge graph edges / entity resolution (Phase 3)
- MCP server bridging (Phase 3)
- Temporal proactive jobs (Phase 3)
- Full OAuth for Google/GitHub/etc. (stubs + permission model only)
