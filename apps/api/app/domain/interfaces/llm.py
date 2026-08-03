from __future__ import annotations

from typing import Protocol


class TextModelProvider(Protocol):
    """Future LLM provider port (Phase 2+).

    Phase 1 realtime speech lives in the agent worker. This API-side port exists so
    control-plane features (summaries, memory extraction) can swap providers later
    without rewriting route handlers.
    """

    async def complete(self, *, system: str, prompt: str) -> str: ...
