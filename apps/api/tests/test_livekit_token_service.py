from __future__ import annotations

import pytest

from app.domain.interfaces.livekit import CreateVoiceSessionRequest
from app.infrastructure.livekit.token_service import LiveKitAccessTokenService


@pytest.mark.asyncio
async def test_token_service_generates_room_and_jwt() -> None:
    service = LiveKitAccessTokenService(
        server_url="wss://example.livekit.cloud",
        api_key="APItestkey",
        api_secret="testsecret_testsecret_testsecret12",
        token_ttl_seconds=120,
    )

    session = await service.create_voice_session(
        CreateVoiceSessionRequest(
            user_id="user_1",
            agent_name="voice-agent",
            language="hi",
        )
    )

    assert session.server_url.startswith("wss://")
    assert session.participant_identity == "user_1"
    assert session.expires_in_seconds == 120
    assert session.room_name.startswith("voice-")
    assert session.participant_token.count(".") == 2

    # JWT payload is middle segment (base64url); language must be embedded for the agent.
    import base64
    import json

    payload_b64 = session.participant_token.split(".")[1]
    padding = "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
    metadata = json.loads(payload["metadata"])
    assert metadata["language"] == "hi"
    room_config = payload.get("roomConfig") or payload.get("room_config")
    assert room_config is not None
    agents = room_config.get("agents") or []
    assert agents
    dispatch_meta = json.loads(agents[0]["metadata"])
    assert dispatch_meta["language"] == "hi"
