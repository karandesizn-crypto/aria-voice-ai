# Phase 2 — implemented

See [PHASE_2_ARCHITECTURE.md](./PHASE_2_ARCHITECTURE.md) for design decisions.

Delivered:

1. Postgres + pgvector schema (Alembic `0001_phase2`)
2. Redis session cache + tool rate limits
3. Memory service: episodic / semantic / preference + turn history + scoring/dedup
4. Tool framework with weather + maps (live/mock) and scaffolded OAuth tools
5. Agent bootstrap loads memory bundle and exposes weather/maps/remember tools via API
