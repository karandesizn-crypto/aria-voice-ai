from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    livekit_url: str = Field(alias="LIVEKIT_URL")
    livekit_api_key: str = Field(alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(alias="LIVEKIT_API_SECRET")

    # groq (default) | openai
    voice_provider: str = Field(default="groq", alias="VOICE_PROVIDER")

    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_llm_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_LLM_MODEL")
    groq_stt_model: str = Field(default="whisper-large-v3-turbo", alias="GROQ_STT_MODEL")
    groq_stt_language: str = Field(default="en", alias="GROQ_STT_LANGUAGE")
    # edge (default, free) | groq (Orpheus — requires accepting terms in Groq console)
    tts_provider: str = Field(default="edge", alias="TTS_PROVIDER")
    edge_tts_voice: str = Field(default="en-US-JennyNeural", alias="EDGE_TTS_VOICE")
    groq_tts_model: str = Field(
        default="canopylabs/orpheus-v1-english",
        alias="GROQ_TTS_MODEL",
    )
    groq_tts_voice: str = Field(default="autumn", alias="GROQ_TTS_VOICE")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_realtime_model: str = Field(default="gpt-realtime", alias="OPENAI_REALTIME_MODEL")
    openai_realtime_voice: str = Field(default="marin", alias="OPENAI_REALTIME_VOICE")

    agent_name: str = Field(default="voice-agent", alias="AGENT_NAME")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    agent_service_token: str = Field(default="dev-agent-token", alias="AGENT_SERVICE_TOKEN")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")


@lru_cache
def get_settings() -> AgentSettings:
    return AgentSettings()  # type: ignore[call-arg]
