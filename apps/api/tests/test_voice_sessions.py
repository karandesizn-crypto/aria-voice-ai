from __future__ import annotations

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.main import create_app


@pytest.mark.asyncio
@respx.mock
async def test_create_voice_session_requires_auth() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/voice/sessions", json={})

    assert response.status_code == 401


@pytest.mark.asyncio
@respx.mock
async def test_create_voice_session_success(
    make_clerk_token,
    jwks_payload: dict,
) -> None:
    respx.get("https://example.clerk.accounts.dev/.well-known/jwks.json").mock(
        return_value=Response(200, json=jwks_payload)
    )

    app = create_app()
    transport = ASGITransport(app=app)
    token = make_clerk_token(sub="user_abc")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/voice/sessions",
            json={"agent_name": "voice-agent"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["server_url"] == "wss://example.livekit.cloud"
    assert body["participant_identity"] == "user_abc"
    assert body["room_name"].startswith("voice-")
    assert isinstance(body["participant_token"], str)
    assert len(body["participant_token"]) > 20
