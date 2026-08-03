# Phase 4 Architecture

## Goal

Extend the platform beyond the web voice surface:

- Mobile client (Expo / React Native) for authenticated talk sessions
- Desktop client (Electron shell) wrapping the web app for always-available voice
- Analytics control-plane metrics (sessions, tool usage, memory growth)
- Multi-agent orchestration (router + specialist agents)

## Design decisions

### 1. Mobile shares API contracts, not web UI

**Decision:** Expo app calls the same FastAPI + LiveKit token flow.

**Why:** Native mic permissions and background constraints differ from Next.js.

### 2. Desktop embeds the web origin

**Decision:** Electron loads `NEXT_PUBLIC_APP_URL` with native window chrome.

**Why:** Avoid duplicating Clerk/LiveKit UI; ship faster with one web surface.

### 3. Analytics derived from existing tables

**Decision:** Aggregate from `conversations`, `tool_invocations`, `memories` — no separate event bus yet.

**Why:** Enough signal for Phase 4; Kafka/ClickHouse can wait.

### 4. Multi-agent via explicit router

**Decision:** A supervisor chooses among named specialists (general, research, scheduling) using lightweight routing rules + optional LLM later.

**Why:** Deterministic, testable orchestration before introducing complex LangGraph graphs.
