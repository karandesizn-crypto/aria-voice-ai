# Phase 3 Architecture

## Goal

Add durable relational intelligence and autonomous background behavior:

- Knowledge graph linking people, projects, goals, tasks, meetings, documents, preferences
- MCP bridge so external tool servers plug into the existing ToolRegistry
- Temporal workflows for proactive reminders and deferred jobs
- Langfuse-ready span hooks around graph/tool/job paths

## Design decisions

### 1. Property graph in Postgres (not Neo4j)

**Decision:** `kg_nodes` + `kg_edges` tables with typed labels and JSON properties.

**Why:** One operational database, transactional writes with memories, simpler local/dev story.

**Tradeoff:** Deep multi-hop queries are less ergonomic than Neo4j. Acceptable for Phase 3 scale; can federate later.

### 2. MCP as a tool provider, not a parallel stack

**Decision:** MCP clients adapt remote tools into the existing `Tool` protocol.

**Why:** Keeps permission checks, retries, and telemetry consistent.

### 3. Temporal for durable jobs; local runner for tests

**Decision:** Reminder workflows run on Temporal when configured; unit tests exercise pure workflow logic with an in-process scheduler.

**Why:** Production needs durability; CI should not require a Temporal cluster.

## Security

- Graph reads/writes are user-scoped (`user_id` on every node).
- MCP servers are allowlisted by URL/command in config.
- Temporal task queues are namespaced per environment.

## Out of scope (Phase 4)

Mobile/desktop clients, analytics product UI, multi-agent orchestration.
