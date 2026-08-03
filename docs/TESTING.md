# How to test Aria locally

## What's already running

If you just asked the agent to run it, these should be up:

| Service | URL |
| --- | --- |
| API | http://127.0.0.1:8000 |
| API docs | http://127.0.0.1:8000/docs |
| Web | http://127.0.0.1:3000 |
| Postgres 17 + pgvector | `127.0.0.1:5432` db `voice` |
| Redis | `127.0.0.1:6379` |

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Fastest path (no cloud keys)

Use the agent service token against the API. This exercises memory, tools, graph, reminders, routing, and analytics.

```bash
TOKEN=dev-agent-token-change-me
USER=demo_user
H=(-H "Authorization: Bearer $TOKEN" -H "X-User-Id: $USER" -H "Content-Type: application/json")

# Tools catalog
curl -s http://127.0.0.1:8000/v1/tools | jq .

# Write + read memory
curl -s -X POST http://127.0.0.1:8000/v1/memory/items "${H[@]}" \
  -d '{"kind":"preference","content":"Prefers short answers","importance":0.9,"user_id":"demo_user"}' | jq .
curl -s "http://127.0.0.1:8000/v1/memory/bundle?user_id=demo_user" "${H[@]}" | jq .

# Mock weather tool
curl -s -X POST http://127.0.0.1:8000/v1/tools/invoke "${H[@]}" \
  -d '{"tool_name":"weather","arguments":{"location":"Austin"},"user_id":"demo_user"}' | jq .

# Knowledge graph
curl -s -X POST http://127.0.0.1:8000/v1/graph/nodes "${H[@]}" \
  -d '{"label":"project","name":"Voice Platform","user_id":"demo_user"}' | jq .

# Multi-agent router
curl -s -X POST http://127.0.0.1:8000/v1/agents/route "${H[@]}" \
  -d '{"utterance":"Remind me about the meeting tomorrow"}' | jq .

# Analytics
curl -s http://127.0.0.1:8000/v1/analytics/summary "${H[@]}" | jq .
```

Or open interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Full voice conversation (needs your keys)

Edit `.env` (and restart API/web/agent) with real values:

1. **Clerk** — `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `CLERK_JWKS_URL`, `CLERK_ISSUER`
2. **LiveKit Cloud** — `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `NEXT_PUBLIC_LIVEKIT_URL`
3. **OpenAI** — `OPENAI_API_KEY` (Realtime + embeddings)

Then run three processes:

```bash
# Terminal 1 — API
cd apps/api && source .venv/bin/activate && set -a && source ../../.env && set +a
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Agent worker
cd apps/agent && source .venv/bin/activate && set -a && source ../../.env && set +a
python -m voice_agent.main start

# Terminal 3 — Web
cd apps/web
# export the NEXT_PUBLIC_* / CLERK_* vars, then:
npm run dev
```

Test flow:

1. Open http://localhost:3000
2. Sign in with Clerk
3. Go to **Talk** → **Start talking** (allow mic)
4. Speak; interrupt mid-sentence to verify barge-in
5. Say “remember that I prefer short answers” then check **Memory**
6. Check **Analytics** for counts

## Mobile / desktop

```bash
# Desktop shell (loads the web app)
cd apps/desktop && npm start   # needs DESKTOP_APP_URL=http://localhost:3000

# Mobile (Expo) — after Clerk token wiring
cd apps/mobile && npx expo start
```

## Automated tests

```bash
cd apps/api && source .venv/bin/activate && pytest
cd apps/agent && source .venv/bin/activate && pytest
cd apps/web && npm test && npm run typecheck
node --test apps/mobile/src/api.test.mjs
node --test apps/desktop/test/main.test.mjs
```

## Restart data plane later

```bash
brew services start postgresql@17
/opt/homebrew/opt/redis/bin/redis-server --port 6379 --daemonize yes --dir /tmp --dbfilename voice-redis.rdb
```
