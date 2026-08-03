# Voice Agent Worker

Joins LiveKit rooms and converses via voice.

## Provider order

1. **Groq** (default, free) — STT `whisper-large-v3-turbo` + LLM `llama-3.3-70b-versatile` + TTS via Edge (`TTS_PROVIDER=edge`) or Groq Orpheus (`TTS_PROVIDER=groq`, requires accepting Orpheus terms in the Groq console)
2. **OpenAI Realtime** — set `VOICE_PROVIDER=openai` and `OPENAI_API_KEY`

## Run locally

```bash
cd apps/agent
source .venv/bin/activate
set -a && source ../../.env && set +a
python -m voice_agent.main start
```

Required: `LIVEKIT_*`, `GROQ_API_KEY` (or OpenAI), `API_BASE_URL`, `AGENT_SERVICE_TOKEN`.
