from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class VoiceSessionToken:
    """Credentials required for a client to join a LiveKit room."""

    server_url: str
    room_name: str
    participant_identity: str
    participant_token: str
    expires_in_seconds: int


@dataclass(frozen=True, slots=True)
class CreateVoiceSessionRequest:
    user_id: str
    room_name: str | None = None
    agent_name: str = "voice-agent"
    language: str = "en"


class LiveKitTokenService(Protocol):
    """Mints short-lived LiveKit access tokens for voice sessions."""

    async def create_voice_session(
        self,
        request: CreateVoiceSessionRequest,
    ) -> VoiceSessionToken: ...
