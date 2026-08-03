from __future__ import annotations

from voice_agent.settings import AgentSettings


def test_default_voice_provider_is_groq() -> None:
    # Defaults on the model fields (without requiring LiveKit env at import time).
    assert AgentSettings.model_fields["voice_provider"].default == "groq"
    assert AgentSettings.model_fields["tts_provider"].default == "edge"
    assert AgentSettings.model_fields["groq_llm_model"].default == "llama-3.3-70b-versatile"
    assert AgentSettings.model_fields["groq_stt_model"].default == "whisper-large-v3-turbo"
    assert (
        AgentSettings.model_fields["groq_tts_model"].default
        == "canopylabs/orpheus-v1-english"
    )
