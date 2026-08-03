from __future__ import annotations

import json
import secrets
import time
from datetime import timedelta

from livekit.api import AccessToken, RoomAgentDispatch, RoomConfiguration, VideoGrants

from app.domain.interfaces.livekit import (
    CreateVoiceSessionRequest,
    LiveKitTokenService,
    VoiceSessionToken,
)


class LiveKitAccessTokenService(LiveKitTokenService):
    """Creates LiveKit room tokens with explicit agent dispatch."""

    def __init__(
        self,
        *,
        server_url: str,
        api_key: str,
        api_secret: str,
        token_ttl_seconds: int = 60 * 60,
    ) -> None:
        self._server_url = server_url
        self._api_key = api_key
        self._api_secret = api_secret
        self._token_ttl_seconds = token_ttl_seconds

    async def create_voice_session(
        self,
        request: CreateVoiceSessionRequest,
    ) -> VoiceSessionToken:
        room_name = request.room_name or self._generate_room_name(request.user_id)
        identity = request.user_id

        token = (
            AccessToken(self._api_key, self._api_secret)
            .with_identity(identity)
            .with_name(identity)
            .with_ttl(timedelta(seconds=self._token_ttl_seconds))
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .with_metadata(
                json.dumps(
                    {
                        "user_id": request.user_id,
                        "agent_name": request.agent_name,
                        "language": request.language,
                    },
                    separators=(",", ":"),
                )
            )
            .with_room_config(
                RoomConfiguration(
                    agents=[
                        RoomAgentDispatch(
                            agent_name=request.agent_name,
                            metadata=json.dumps(
                                {
                                    "user_id": request.user_id,
                                    "language": request.language,
                                },
                                separators=(",", ":"),
                            ),
                        )
                    ]
                )
            )
        )

        return VoiceSessionToken(
            server_url=self._server_url,
            room_name=room_name,
            participant_identity=identity,
            participant_token=token.to_jwt(),
            expires_in_seconds=self._token_ttl_seconds,
        )

    def _generate_room_name(self, user_id: str) -> str:
        suffix = secrets.token_hex(4)
        safe_user = user_id.replace("|", "-")[:24]
        return f"voice-{safe_user}-{int(time.time())}-{suffix}"
