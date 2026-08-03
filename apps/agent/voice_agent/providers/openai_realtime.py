from __future__ import annotations

from livekit.plugins import openai
from openai.types.beta.realtime.session import TurnDetection

from voice_agent.settings import AgentSettings


class OpenAIRealtimeProvider:
    """OpenAI Realtime API adapter with semantic VAD + barge-in (fallback path)."""

    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings

    def create(self):
        if not self._settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when VOICE_PROVIDER=openai")
        return openai.realtime.RealtimeModel(
            model=self._settings.openai_realtime_model,
            voice=self._settings.openai_realtime_voice,
            api_key=self._settings.openai_api_key,
            turn_detection=TurnDetection(
                type="semantic_vad",
                eagerness="medium",
                create_response=True,
                interrupt_response=True,
            ),
        )
