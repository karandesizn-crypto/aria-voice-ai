from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import httpx
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.domain.interfaces.livekit import LiveKitTokenService
from app.domain.models import ClerkUser
from app.infrastructure.auth.clerk import ClerkAuthProvider
from app.infrastructure.livekit.token_service import LiveKitAccessTokenService
from app.infrastructure.tools.registry import ToolRegistry
from app.services.memory_service import MemoryService

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    is_agent: bool = False


def get_http_client(request: Request) -> httpx.AsyncClient:
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        client = httpx.AsyncClient(timeout=20.0)
        request.app.state.http_client = client
    return client


def get_auth_provider(
    settings: Annotated[Settings, Depends(get_settings)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> ClerkAuthProvider:
    return ClerkAuthProvider(
        jwks_url=settings.clerk_jwks_url,
        issuer=settings.clerk_issuer,
        audience=settings.clerk_audience,
        http_client=http_client,
    )


def get_livekit_token_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LiveKitTokenService:
    return LiveKitAccessTokenService(
        server_url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth_provider: Annotated[ClerkAuthProvider, Depends(get_auth_provider)],
) -> ClerkUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await auth_provider.verify_token(credentials.credentials)


async def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
    auth_provider: Annotated[ClerkAuthProvider, Depends(get_auth_provider)],
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> Principal:
    """Accept Clerk user JWT or agent service token (+ X-User-Id)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = credentials.credentials
    if token == settings.agent_service_token:
        if not x_user_id:
            raise HTTPException(status_code=400, detail="X-User-Id required for agent calls")
        return Principal(user_id=x_user_id, is_agent=True)

    user = await auth_provider.verify_token(token)
    return Principal(user_id=user.user_id, is_agent=False)


def get_memory_service(request: Request) -> MemoryService:
    service = getattr(request.app.state, "memory_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Memory service unavailable")
    return service


def get_tool_registry(request: Request) -> ToolRegistry:
    registry = getattr(request.app.state, "tool_registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Tool registry unavailable")
    return registry


def resolve_user_id(principal: Principal, body_user_id: str | None) -> str:
    if principal.is_agent:
        if not body_user_id:
            raise HTTPException(status_code=400, detail="user_id required for agent calls")
        return body_user_id
    return principal.user_id
