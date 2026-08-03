from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_livekit_token_service
from app.api.schemas import CreateSessionBody, VoiceSessionResponse
from app.core.logging import get_logger
from app.domain.interfaces.livekit import (
    CreateVoiceSessionRequest,
    LiveKitTokenService,
)
from app.domain.models import ClerkUser

router = APIRouter(prefix="/v1/voice", tags=["voice"])
logger = get_logger(__name__)


@router.post(
    "/sessions",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_voice_session(
    body: CreateSessionBody,
    user: Annotated[ClerkUser, Depends(get_current_user)],
    token_service: Annotated[LiveKitTokenService, Depends(get_livekit_token_service)],
) -> VoiceSessionResponse:
    language = (body.language or "en").strip().lower()
    session = await token_service.create_voice_session(
        CreateVoiceSessionRequest(
            user_id=user.user_id,
            room_name=body.room_name,
            agent_name=body.agent_name,
            language=language,
        )
    )

    logger.info(
        "voice_session_created",
        user_id=user.user_id,
        room_name=session.room_name,
        agent_name=body.agent_name,
        language=language,
    )

    return VoiceSessionResponse(
        server_url=session.server_url,
        room_name=session.room_name,
        participant_identity=session.participant_identity,
        participant_token=session.participant_token,
        expires_in_seconds=session.expires_in_seconds,
    )
