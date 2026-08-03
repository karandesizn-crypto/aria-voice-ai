from __future__ import annotations

from livekit.plugins import groq, silero

from voice_agent.languages import VoiceLanguage, resolve_language
from voice_agent.providers.edge_tts import EdgeTTS
from voice_agent.settings import AgentSettings


class GroqVoicePipelineProvider:
    """Groq STT + LLM with Edge TTS (multilingual) or optional Groq Orpheus TTS."""

    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings

    def create_session_kwargs(self, *, language: str | None = None) -> dict:
        api_key = self._settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY is required when VOICE_PROVIDER=groq")

        locale = resolve_language(language or self._settings.groq_stt_language)

        return {
            "stt": groq.STT(
                model=self._settings.groq_stt_model,
                api_key=api_key,
                language=locale.stt_code,
            ),
            "llm": groq.LLM(
                model=self._settings.groq_llm_model,
                api_key=api_key,
            ),
            "tts": self._build_tts(locale),
            "vad": silero.VAD.load(),
        }

    def _build_tts(self, locale: VoiceLanguage):
        # Multilingual voice chat always uses Edge Neural voices.
        # Groq Orpheus remains available only for explicit English groq TTS mode.
        provider = (self._settings.tts_provider or "edge").lower()
        if provider == "groq" and locale.code == "en":
            return groq.TTS(
                model=self._settings.groq_tts_model,
                voice=self._settings.groq_tts_voice,
                api_key=self._settings.groq_api_key,
            )
        return EdgeTTS(voice=locale.edge_voice)
