# Phase 1 Architecture

## Goal

Ship a production-shaped foundation for realtime voice conversations:

- Authenticated users join a LiveKit room from the web app
- A Python agent worker joins the same room and speaks via OpenAI Realtime
- FastAPI owns the control plane (auth, tokens, session metadata)
- Media never traverses FastAPI

## System diagram

```text
┌─────────────────┐     HTTPS/JWT      ┌──────────────────┐
│  Next.js (web)  │ ─────────────────▶ │  FastAPI (api)   │
│  Clerk + LiveKit│ ◀── LiveKit token ─│  Clerk verify    │
│  Components     │                    │  LiveKit mint    │
└────────┬────────┘                    └──────────────────┘
         │ WebRTC (audio)
         ▼
┌─────────────────┐   agent dispatch   ┌──────────────────┐
│  LiveKit SFU    │ ◀─────────────────▶│  Agent worker    │
│  rooms / tracks │                    │  OpenAI Realtime │
└─────────────────┘                    └────────┬─────────┘
                                                │ WebSocket
                                                ▼
                                       ┌──────────────────┐
                                       │ OpenAI Realtime  │
                                       │ semantic VAD +   │
                                       │ interruption     │
                                       └──────────────────┘
```

## Layer boundaries

| Layer | Package | Responsibility in Phase 1 |
| --- | --- | --- |
| Frontend | `apps/web` | Auth UI, voice session UI, LiveKit client |
| Control API | `apps/api` | JWT auth, LiveKit tokens, health, session create |
| Agent | `apps/agent` | Room participant, Realtime model, turn handling |
| Memory | stub interfaces only | Wired in Phase 2 |
| Tools | stub interfaces only | Wired in Phase 2 |

## Design decisions

### 1. Split control plane and media plane

**Decision:** FastAPI never proxies audio.

**Why:** Sub-second voice requires WebRTC edge paths. Putting media through the API adds hops, serialization cost, and a single bottleneck.

**Tradeoff:** Two deployables (API + agent) instead of one. Operational complexity rises slightly; latency and scale improve.

### 2. LiveKit + OpenAI Realtime (not browser-direct Realtime)

**Decision:** Browser talks to LiveKit; the agent worker talks to OpenAI Realtime.

**Why:** LiveKit gives interruption handling, multi-party rooms, recording hooks, and a stable WebRTC client story. Keeping OpenAI keys off the browser is mandatory for production.

**Tradeoff:** Extra infra (LiveKit Cloud or self-hosted). Worth it for a platform, not a demo.

### 3. Thin provider interfaces, one implementation

**Decision:** `RealtimeModelProvider` and `TokenService` protocols exist; only OpenAI / LiveKit implementations ship now.

**Why:** Requirement to support multiple LLM providers later, without inventing a plugin framework yet.

**Tradeoff:** A few extra files. Avoided deeper DI containers / service locators.

### 4. Clerk as the identity source of truth

**Decision:** Web uses Clerk; API verifies Clerk JWTs (JWKS). Agent receives only trusted room metadata from LiveKit (user id in token grants).

**Why:** Avoid custom auth in Phase 1. Clerk already covers sessions, MFA, and org models for later multi-tenant work.

**Tradeoff:** Vendor lock-in on identity. Acceptable; identity adapters can wrap Clerk later if needed.

### 5. Semantic VAD with interruptible responses

**Decision:** OpenAI Realtime `semantic_vad` + `interrupt_response=True`.

**Why:** Natural barge-in without building a custom turn detector in Phase 1. LiveKit still owns transport-level audio.

**Tradeoff:** Turn quality depends on OpenAI VAD. Phase 2+ can add LiveKit turn detector / hybrid strategies if needed.

### 6. Monorepo with three apps

**Decision:** `apps/web`, `apps/api`, `apps/agent` under one repo; npm workspaces for JS; uv/pip for Python apps.

**Why:** Shared docs, CI, and env conventions without premature shared libraries.

**Tradeoff:** No shared TS/Python package yet. Add `packages/*` when duplication appears (Phase 2 schemas).

## Scalability

- **Horizontal:** Agent workers scale independently via LiveKit job dispatch. API is stateless and horizontally scalable behind a load balancer.
- **LiveKit SFU:** Media fan-out is LiveKit's problem; we do not reinvent peer mesh.
- **Session affinity:** Not required for API. Agent jobs are room-scoped.
- **Phase 2 readiness:** Redis (session cache), Postgres (users/memories), pgvector (semantic recall) plug in behind existing interfaces without changing the media path.

## Security

- OpenAI and LiveKit secrets stay server-side (API + agent only).
- LiveKit tokens are short-lived, room-scoped, and identity-bound to Clerk `user_id`.
- CORS restricted to the web origin.
- Structured request IDs on every API call; no secrets in logs.
- Clerk webhook / org RBAC deferred to later phases; Phase 1 enforces authenticated user for token minting.

## Explicitly out of scope (Phase 1)

- Persistent memory / knowledge graph
- Tool framework implementations
- Temporal / proactive jobs
- Mobile / desktop clients
- Multi-agent orchestration

## Success criteria

1. Signed-in user can start a voice session from the web UI
2. Agent greets and holds a natural interrupted conversation
3. API health + token endpoints are tested
4. Local Docker Compose (or Cloud LiveKit) boots the stack with documented env vars
5. CI runs lint/typecheck/unit tests for web + api
