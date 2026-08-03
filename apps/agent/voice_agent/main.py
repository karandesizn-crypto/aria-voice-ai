from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, cli, room_io

from voice_agent.assistant import VoiceAssistant, _format_bundle
from voice_agent.languages import resolve_language
from voice_agent.orchestration import SPECIALIST_INSTRUCTIONS
from voice_agent.platform_client import PlatformApiClient
from voice_agent.providers.groq_pipeline import GroqVoicePipelineProvider
from voice_agent.providers.openai_realtime import OpenAIRealtimeProvider
from voice_agent.settings import get_settings

load_dotenv(".env")
load_dotenv(".env.local")
load_dotenv("../../.env")

logger = logging.getLogger("voice-agent")
AGENT_NAME = os.getenv("AGENT_NAME", "voice-agent")

server = AgentServer()


def _participant_user_id(ctx: JobContext) -> str:
    for participant in ctx.room.remote_participants.values():
        identity = participant.identity
        if identity:
            return identity
        if participant.metadata:
            try:
                payload = json.loads(participant.metadata)
                if payload.get("user_id"):
                    return str(payload["user_id"])
            except json.JSONDecodeError:
                pass
    return "anonymous"


def _session_language(ctx: JobContext) -> str:
    """Prefer agent dispatch metadata, then participant metadata."""
    raw = getattr(ctx.job, "metadata", None) or ""
    if raw:
        try:
            payload = json.loads(raw)
            if payload.get("language"):
                return str(payload["language"])
        except json.JSONDecodeError:
            pass

    for participant in ctx.room.remote_participants.values():
        if not participant.metadata:
            continue
        try:
            payload = json.loads(participant.metadata)
            if payload.get("language"):
                return str(payload["language"])
        except json.JSONDecodeError:
            continue
    return "en"


def _resolve_provider(settings) -> str:
    provider = (settings.voice_provider or "groq").lower()
    if provider == "groq" and settings.groq_api_key:
        return "groq"
    if provider == "openai" and settings.openai_api_key:
        return "openai"
    if settings.groq_api_key:
        return "groq"
    if settings.openai_api_key:
        return "openai"
    raise RuntimeError("No voice provider configured. Set GROQ_API_KEY or OPENAI_API_KEY.")


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    settings = get_settings()
    provider_name = _resolve_provider(settings)
    language_code = _session_language(ctx)
    locale = resolve_language(language_code)

    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": settings.agent_name,
        "environment": settings.environment,
        "voice_provider": provider_name,
        "language": locale.code,
    }

    await ctx.connect()
    user_id = _participant_user_id(ctx)
    # Re-read after connect in case participant metadata arrived with the joiner.
    language_code = _session_language(ctx)
    locale = resolve_language(language_code)

    api_client = PlatformApiClient(
        base_url=settings.api_base_url,
        service_token=settings.agent_service_token,
        user_id=user_id,
    )

    memory_context = "Known user context:\n- No stored memories yet."
    conversation_id: str | None = None
    try:
        bundle = await api_client.get_memory_bundle(room_name=ctx.room.name)
        memory_context = _format_bundle(bundle)
        conversation_id = await api_client.start_conversation(ctx.room.name)
    except Exception:  # noqa: BLE001
        logger.exception("memory_bootstrap_failed")

    specialist = SPECIALIST_INSTRUCTIONS["general"]
    language_rule = (
        f"Always speak and reply in {locale.label}. "
        "Match the user's language choice even if they mix in English words."
    )
    enriched_memory = (
        f"{memory_context}\n\nActive specialist:\n{specialist}\n\nLanguage:\n{language_rule}"
    )

    if provider_name == "groq":
        logger.info("using_groq_pipeline language=%s voice=%s", locale.code, locale.edge_voice)
        session = AgentSession(
            **GroqVoicePipelineProvider(settings).create_session_kwargs(language=locale.code)
        )
        agent = VoiceAssistant(api_client=api_client, memory_context=enriched_memory)
    else:
        logger.info("using_openai_realtime language=%s", locale.code)
        realtime_model = OpenAIRealtimeProvider(settings).create()
        session = AgentSession()
        agent = VoiceAssistant(
            api_client=api_client,
            memory_context=enriched_memory,
            realtime_model=realtime_model,
        )

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(),
        ),
    )

    logger.info(
        "agent_connected room=%s user_id=%s provider=%s language=%s",
        ctx.room.name,
        user_id,
        provider_name,
        locale.code,
    )

    await session.generate_reply(
        instructions=(
            f"{locale.greeting_instruction} If memory context includes their name or "
            "preferences, use them naturally without mentioning the memory system."
        ),
    )

    if conversation_id:
        try:
            await api_client.append_turn(
                conversation_id=conversation_id,
                room_name=ctx.room.name,
                role="system",
                content=f"voice_session_started:{provider_name}:{locale.code}",
            )
        except Exception:  # noqa: BLE001
            logger.exception("session_turn_persist_failed")


def main() -> None:
    cli.run_app(server)


if __name__ == "__main__":
    main()
