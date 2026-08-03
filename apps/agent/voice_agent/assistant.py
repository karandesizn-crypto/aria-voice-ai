from __future__ import annotations

import json
import logging
from typing import Any

from livekit.agents import Agent, RunContext, function_tool

from voice_agent.platform_client import PlatformApiClient
from voice_agent.prompts import AGENT_INSTRUCTIONS


def _format_bundle(bundle: dict[str, Any]) -> str:
    prefs = bundle.get("preferences") or []
    semantic = bundle.get("semantic") or []
    episodic = bundle.get("episodic") or []
    lines = ["Known user context:"]
    for item in prefs[:6]:
        content = item["content"] if isinstance(item, dict) else str(item)
        lines.append(f"- Preference: {content}")
    for item in semantic[:6]:
        content = item["content"] if isinstance(item, dict) else str(item)
        lines.append(f"- Fact: {content}")
    for item in episodic[:6]:
        content = item["content"] if isinstance(item, dict) else str(item)
        lines.append(f"- Recent: {content}")
    if len(lines) == 1:
        lines.append("- No stored memories yet.")
    return "\n".join(lines)


class VoiceAssistant(Agent):
    def __init__(
        self,
        *,
        api_client: PlatformApiClient,
        memory_context: str,
        realtime_model: Any | None = None,
    ) -> None:
        instructions = f"{AGENT_INSTRUCTIONS}\n\n{memory_context}"
        if realtime_model is not None:
            super().__init__(instructions=instructions, llm=realtime_model)
        else:
            # Pipeline mode: STT/LLM/TTS live on AgentSession.
            super().__init__(instructions=instructions)
        self._api = api_client
        self._logger = logging.getLogger("voice-agent.tools")

    @function_tool
    async def lookup_weather(self, context: RunContext, location: str) -> str:
        """Look up current weather for a city or location."""
        result = await self._api.invoke_tool("weather", {"location": location})
        return json.dumps(result)

    @function_tool
    async def lookup_place(self, context: RunContext, query: str) -> str:
        """Geocode a place name or address."""
        result = await self._api.invoke_tool("maps", {"query": query})
        return json.dumps(result)

    @function_tool
    async def remember_fact(
        self,
        context: RunContext,
        content: str,
        kind: str = "semantic",
    ) -> str:
        """Store an important user fact, preference, or episode for later sessions."""
        if kind not in {"semantic", "preference", "episodic"}:
            kind = "semantic"
        try:
            stored = await self._api.write_memory(kind=kind, content=content, importance=0.75)
            return json.dumps({"ok": True, "stored": stored.get("content", content), "kind": kind})
        except Exception as exc:  # noqa: BLE001
            self._logger.warning("remember_fact_failed error=%s", exc)
            return json.dumps({"ok": False, "error": str(exc)})
