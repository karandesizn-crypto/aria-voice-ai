from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import Principal, get_principal
from app.api.schemas_phase34 import AnalyticsResponse, RouteBody, RouteResponse
from app.services.analytics_service import AnalyticsService
from app.services.orchestration import SPECIALIST_INSTRUCTIONS, AgentRouter

router = APIRouter(tags=["phase4"])


def get_analytics(request: Request) -> AnalyticsService:
    service = getattr(request.app.state, "analytics_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Analytics unavailable")
    return service


@router.get("/v1/analytics/summary", response_model=AnalyticsResponse)
async def analytics_summary(
    principal: Annotated[Principal, Depends(get_principal)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics)],
    days: int = 7,
) -> AnalyticsResponse:
    snap = await analytics.snapshot(clerk_user_id=principal.user_id, days=days)
    return AnalyticsResponse(
        conversations=snap.conversations,
        memories=snap.memories,
        tool_invocations=snap.tool_invocations,
        tool_success_rate=snap.tool_success_rate,
        top_tools=snap.top_tools,
        generated_at=snap.generated_at,
    )


@router.post("/v1/agents/route", response_model=RouteResponse)
async def route_agent(
    body: RouteBody,
    principal: Annotated[Principal, Depends(get_principal)],
) -> RouteResponse:
    decision = AgentRouter().route(body.utterance)
    return RouteResponse(
        agent=decision.agent,
        reason=decision.reason,
        confidence=decision.confidence,
        instructions=SPECIALIST_INSTRUCTIONS[decision.agent],
    )
