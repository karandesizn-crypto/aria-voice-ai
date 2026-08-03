from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


class CreateSessionBody(BaseModel):
    room_name: str | None = Field(
        default=None,
        description="Optional explicit room name. Generated when omitted.",
    )
    agent_name: str = Field(
        default="voice-agent",
        description="LiveKit agent name used for room dispatch.",
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=16,
        description="BCP-47 / ISO language code for STT + TTS (e.g. en, hi, es).",
    )


class VoiceSessionResponse(BaseModel):
    server_url: str
    room_name: str
    participant_identity: str
    participant_token: str
    expires_in_seconds: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str
